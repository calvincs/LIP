import logging
from concurrent.futures import ThreadPoolExecutor
from logging.handlers import RotatingFileHandler
import functools
import socket
import os
import threading
import json
import time
import traceback
import glob
from typing import List, Any, Optional


class LIPCModule:
    def __init__(self, log_level=logging.INFO):
        self.server_started = False
        self.lru_enabled = False
        self.cached_func = None
        self.log_level = log_level


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
        print(f"Starting server thread for {socket_path}")
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

                json_data = json.loads(data.decode("utf-8"))
                args = json_data.get("args", [])
                kwargs = json_data.get("kwargs", {})

                start_time = time.time()
                if self.lru_enabled:
                    result = self.cached_func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                end_time = time.time()

                elapsed_time = end_time - start_time

                try:
                    conn.sendall(json.dumps({"result": result}).encode("utf-8"))
                except BrokenPipeError:
                    self.logger.warning("Client disconnected, continuing...")

                # Log execution information
                log_message = f"{func.__name__} called with args: {args}, kwargs: {kwargs}, time: {elapsed_time:.4f} seconds, lru_enabled: {self.lru_enabled}"
                self.logger.debug(log_message)

            except Exception as e:
                self.logger.error(traceback.print_exc())


    def __call__(self, func):
        # Derive the socket_path based on the function name
        socket_path = f"/tmp/lipcm-{func.__name__}.sock"

        # Set up logging
        self.logger = self.setup_logging(func.__name__)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            init_server = kwargs.pop('init', False)
            lru = kwargs.pop('lru', False)
            lru_size = kwargs.pop('lru_size', None)
            should_exit = kwargs.pop('exit', False)

            if lru and not self.lru_enabled:
                self.cached_func = functools.lru_cache(maxsize=lru_size)(func)
                self.lru_enabled = True

            if should_exit and self.server_started:
                return

            if init_server and not self.server_started:
                self.logger.info(f"Starting server thread for {socket_path} for function {func.__name__}")
                self.start_server(socket_path, func)
                return socket_path

            return func(*args, **kwargs)

        return wrapper



class LIPCClient:
    def __init__(self):
        self.sockets = self.scan_sockets()

    def scan_sockets(self) -> dict:
        socket_paths = glob.glob('/tmp/lipcm-*.sock')
        sockets = {}
        for socket_path in socket_paths:
            func_name = os.path.basename(socket_path)[len('lipcm-'):-len('.sock')]
            sockets[func_name] = {"socket_path":socket_path, "func_name":func_name}
        return sockets

    def refresh_sockets(self) -> None:
        self.sockets = self.scan_sockets()

    def call_function(self, func_name: str, *args, **kwargs) -> Optional[Any]:
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
                s.sendall(json.dumps({"args": args, "kwargs": kwargs}).encode("utf-8"))

                data = s.recv(1024)
                if not data:
                    return None

                json_data = json.loads(data.decode("utf-8"))
                return json_data.get("result", None)

        except Exception:
            print(traceback.print_exc())
            raise

    def list_functions(self) -> List[str]:
        return list(self.sockets.keys())
