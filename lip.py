import logging
from concurrent.futures import ThreadPoolExecutor
from logging.handlers import RotatingFileHandler
import functools
from functools import lru_cache
import socket
import os
import time
import traceback
import glob
from typing import List, Any, Optional
import cbor2
import inspect
import multiprocessing


class LIPModule:
    """
        This class is used to decorate functions that will be run as a server.
        The decorator will start a server process that will listen for connections
        on a Unix socket. The server process will handle incoming connections
        and execute the decorated function with the provided arguments and keyword
        arguments. The result of the function will be returned to the client.

        :param log_level: The log level for the server process.
        :param lru: Enable Least Recently Used (LRU) caching for the function.
        :param lru_max: The maximum number of items to store in the LRU cache.

        :return: The result of the function.
    """


    def __init__(self, log_level: int = logging.INFO, lru: bool = False, lru_max: int = 0):
        """
            This function initializes the LIPModule class.

            :param log_level: The log level for the server process.
            :param lru: Enable Least Recently Used (LRU) caching for the function.
            :param lru_max: The maximum number of items to store in the LRU cache.

            :return: None
        """
        self.server_started = False
        self.log_level = log_level
        self.lru = lru
        self.lru_max = lru_max if lru_max > 0 else None


    def setup_logging(self, func_name: str) -> logging.Logger:
        """
            This function sets up logging for the server process.

            :param func_name: The name of the function being decorated.

            :return: The logger object.
        """
        log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        log_filename = f"log_{func_name}.log"
        log_handler = RotatingFileHandler(log_filename, maxBytes=10*1024*1024, backupCount=5)
        log_handler.setFormatter(log_formatter)
        logger = logging.getLogger(func_name)
        logger.setLevel(self.log_level)
        logger.addHandler(log_handler)
        return logger


    def start_server(self, socket_path: str, func: callable) -> None:
        """
            This function starts the server process.

            :param socket_path: The path to the Unix socket.
            :param func: The function to be decorated.

            :return: None
        """
        self.logger.info(f"Starting server thread for {socket_path} for function {func.__name__}")
        self.server_process = multiprocessing.Process(target=self.server_handler, args=(socket_path, func))
        self.server_process.start()


    def terminate(self) -> None:
        """
            This function terminates the server process.

            :return: None
        """
        if self.server_process is not None:
            self.server_process.terminate()
            self.server_process.join()
            socket_path = f"/tmp/lipcm-{self.server_process.name}.sock"
            try:
                os.unlink(socket_path)
                self.logger.info(f"Removed socket entry for {self.server_process.name}")
            except OSError:
                if os.path.exists(socket_path):
                    self.logger.warning(f"Failed to remove socket entry for {self.server_process.name}")


    def server_handler(self, socket_path: str, func: callable) -> None:
        """
            This function starts the server and handles incoming connections.

            :param socket_path: The path to the Unix socket.
            :param func: The function to be decorated.

            :return: None
        """
        try:
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
        
        except Exception as e:
            log_message = f"Server process for {func.__name__} encountered an error: {str(traceback.format_exc())}"
            self.logger.error(log_message)


    def connection_handler(self, conn: socket.socket, func: callable) -> None:
        """
            This function handles the connection to the client.

            :param conn: The connection object.
            :param func: The function to be decorated.

            :return: None
        """
        with conn:
            try:
                # Receive the data from the client, chunk by chunk if necessary
                data = b''
                while True:
                    chunk = conn.recv(1024)
                    if not chunk:
                        break
                    data += chunk
                    if len(chunk) < 1024:
                        break
                if not data:
                    return

                # Decode the data and extract the arguments, keyword arguments, and request type
                enc_data = cbor2.loads(data)
                args = enc_data.get("args", [])
                kwargs = enc_data.get("kwargs", {})
                request_type = enc_data.get("type", "call")

                # If the request type is docstring, return the docstring
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


    def __call__(self, func: callable):
        """
            This function is called when the decorator is used.

            :param func: The function to be decorated.

            :return: The wrapper function.
        """
        # Derive the socket_path based on the function name
        socket_path = f"/tmp/lipcm-{func.__name__}.sock"

        # Set up logging
        self.logger = self.setup_logging(func.__name__)

        if self.lru:
            func = lru_cache(self.lru_max)(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> callable:
            init_server = kwargs.pop('init', False)

            if init_server:
                self.logger.info(f"Starting server process for {socket_path} for function {func.__name__}")
                self.start_server(socket_path, func)
                return self

            return func(*args, **kwargs)

        return wrapper



class LIPClient:
    """
        This class is used to call functions that are decorated with the LIPModule decorator.
        The client will connect to the server process via a Unix socket and send the arguments
        and keyword arguments to the server. The server will execute the function and return
        the result to the client.

        :return: The result of the function.
    """


    def __init__(self):
        """
            This function initializes the LIPClient class.

            :return: None
        """
        self.sockets = self.scan_sockets()


    def scan_sockets(self) -> dict:
        """
            This function scans the /tmp directory for Unix sockets that are used by the server processes.

            :return: A dictionary of sockets.
        """
        socket_paths = glob.glob('/tmp/lipcm-*.sock')
        sockets = {}
        for socket_path in socket_paths:
            func_name = os.path.basename(socket_path)[len('lipcm-'):-len('.sock')]
            sockets[func_name] = {"socket_path": socket_path, "func_name": func_name}
        return sockets


    def refresh_sockets(self) -> None:
        """
            This function refreshes the list of available sockets (functions).

            :return: None
        """
        self.sockets = self.scan_sockets()


    def get_docstring(self, func_name: str) -> Optional[str]:
        """
            This function returns the docstring for the specified function.

            :param func_name: The name of the function to get the docstring for.

            :return: The docstring for the function.
        """
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
        """
            This function calls the specified function with the provided arguments and keyword arguments.

            :param func_name: The name of the function to call.
            :param args: A list of arguments to pass to the function.
            :param kwargs: A dictionary of keyword arguments to pass to the function.

            :return: The result of the function.
        """
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

                # Receive the data from the server, chunk by chunk if necessary
                data = b''
                while True:
                    chunk = s.recv(1024)
                    if not chunk:
                        break
                    data += chunk
                    if len(chunk) < 1024:
                        break
                if not data:
                    return None

                data = cbor2.loads(data)
                if "error" in data:
                    raise ValueError(data["error"])
                
                return data.get("result", None)

        except ConnectionRefusedError as e:
            raise ConnectionError(f"Could not connect to socket at {socket_path}: {e}") from e

        except Exception:
            print(traceback.print_exc())
            raise


    def list_functions(self) -> List[str]:
        """
            This function returns a list of available functions.

            :return: A list of available functions.
        """
        return list(self.sockets.keys())
