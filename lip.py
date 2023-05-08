import logging
from concurrent.futures import ThreadPoolExecutor
from logging.handlers import RotatingFileHandler
import functools
from functools import lru_cache
import socket
import os
import threading
import time
import traceback
import glob
from typing import List, Any, Optional
import cbor2
import inspect

class LIPModule:
    def __init__(self, log_level=logging.INFO, lru=False, lru_max=0):
        self.server_started = False
        self.log_level = log_level
        self.lru = lru
        self.lru_max = lru_max if lru_max > 0 else None


    def setup_logging(self, func_name):
        log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        log_filename = f"log_{func_name}.log"
        log_handler = RotatingFileHandler(log_filename, maxBytes=10*1024*1024, backupCount=5)
        log_handler.setFormatter(log_formatter)
        logger = logging.getLogger(func_name)
        logger.setLevel(self.log_level)
        logger.addHandler(log_handler)
        return logger


    def start_server(self, socket_path, func):
        self.logger.info(f"Starting server thread for {socket_path} for function {func.__name__}")
        server_thread = threading.Thread(target=self.server_handler, args=(socket_path, func))
        server_thread.daemon = True
        server_thread.start()
        self.server_started = True


    def server_handler(self, socket_path, func):
        with ThreadPoolExecutor() as executor:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                try:
                    os.unlink(socket_path)
                except OSError:
                    if os.path.exists(socket_path):
                        raise

                s.bind(socket_path)
                s.listen(1)

                while True:
                    conn, addr = s.accept()
                    executor.submit(self.connection_handler, conn, func)


    def connection_handler(self, conn, func):
        with conn:
            try:
                data = conn.recv(1024)
                if not data:
                    return

                enc_data = cbor2.loads(data)
                args = enc_data.get("args", [])
                kwargs = enc_data.get("kwargs", {})
                request_type = enc_data.get("type", "call")

                if request_type == "docstring":
                    conn.sendall(cbor2.dumps({"result": func.__doc__}))
                    return
                
                # Validate arguments and keyword arguments
                sig = inspect.signature(func)
                try:
                    sig.bind(*args, **kwargs)
                except TypeError as e:
                    self.logger.error(f"Invalid arguments or keyword arguments: {str(e)}")
                    conn.sendall(cbor2.dumps({"error": str(e)}))
                    return

                # Execute the function, catching any exceptions, and return the result
                try:
                    start_time = time.time()
                    result = func(*args, **kwargs)
                    end_time = time.time()
                    elapsed_time = end_time - start_time

                    # Log execution information
                    log_message = f"{func.__name__} called with args: {args}, kwargs: {kwargs}, time: {elapsed_time:.4f} seconds"
                    self.logger.debug(log_message)

                except Exception as e:
                    log_message = f"{func.__name__} called with args: {args}, kwargs: {kwargs}, error: {str(traceback.format_exc())}"
                    self.logger.error(log_message)
                    conn.sendall(cbor2.dumps({"error": str(e)}))
                    return

                try:
                    conn.sendall(cbor2.dumps({"result": result}))
                except BrokenPipeError:
                    self.logger.warning("Client disconnected...")

            except Exception as e:
                log_message = f"{func.__name__} uncaught exception: {str(e)} in connection_handler: {traceback.format_exc()}"
                self.logger.error(traceback.format_exc())


    def __call__(self, func):
        # Derive the socket_path based on the function name
        socket_path = f"/tmp/lipcm-{func.__name__}.sock"

        # Set up logging
        self.logger = self.setup_logging(func.__name__)

        if self.lru:
            func = lru_cache(self.lru_max)(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            init_server = kwargs.pop('init', False)
            should_exit = kwargs.pop('exit', False)

            if should_exit and self.server_started:
                return

            if init_server and not self.server_started:
                self.logger.info(f"Starting server thread for {socket_path} for function {func.__name__}")
                self.start_server(socket_path, func)
                return socket_path

            return func(*args, **kwargs)

        return wrapper



class LIPClient:
    def __init__(self):
        self.sockets = self.scan_sockets()

    def scan_sockets(self) -> dict:
        socket_paths = glob.glob('/tmp/lipcm-*.sock')
        sockets = {}
        for socket_path in socket_paths:
            func_name = os.path.basename(socket_path)[len('lipcm-'):-len('.sock')]
            sockets[func_name] = {"socket_path": socket_path, "func_name": func_name}
        return sockets

    def refresh_sockets(self) -> None:
        self.sockets = self.scan_sockets()


    def get_docstring(self, func_name: str) -> Optional[str]:
        if func_name not in self.sockets:
            raise ValueError(f"Function '{func_name}' not found in available sockets.")

        socket_path = self.sockets[func_name]["socket_path"]

        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.connect(socket_path)
                s.sendall(cbor2.dumps({"type": "docstring"}))

                data = s.recv(1024)
                if not data:
                    return None

                data = cbor2.loads(data)
                return data.get("result", None)

        except Exception:
            print(traceback.print_exc())
            raise


    def call_function(self, func_name: str, args: List[Any] = None, kwargs: dict = None) -> Optional[Any]:
        if args is None:
            args = []

        if kwargs is None:
            kwargs = {}

        if func_name not in self.sockets:
            raise ValueError(f"Function '{func_name}' not found in available sockets.")

        socket_path = self.sockets[func_name]["socket_path"]

        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.connect(socket_path)
                s.sendall(cbor2.dumps({"args": args, "kwargs": kwargs}))

                data = s.recv(1024)
                if not data:
                    return None

                data = cbor2.loads(data)
                if "error" in data:
                    raise ValueError(data["error"])
                
                return data.get("result", None)

        except Exception:
            print(traceback.print_exc())
            raise

    def list_functions(self) -> List[str]:
        return list(self.sockets.keys())
