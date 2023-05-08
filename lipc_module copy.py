import socket
import functools
import json
import os
import threading
import time
import traceback
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler


class LIPCModule:
    def __init__(self):
        self.server_started = False
        self.lru_enabled = False
        self.cached_func = None

    def __call__(self, func):
        # Derive the socket_path based on the function name
        socket_path = f"/tmp/lipcm-{func.__name__}.sock"

        # Set up logging
        log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        log_filename = f"log_{func.__name__}.log"
        log_handler = RotatingFileHandler(log_filename, maxBytes=10*1024*1024, backupCount=5)
        log_handler.setFormatter(log_formatter)

        logger = logging.getLogger(func.__name__)
        logger.setLevel(logging.INFO)
        logger.addHandler(log_handler)

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
                print(f"Starting server thread for {socket_path}")
                server_thread = threading.Thread(target=wrapper)
                server_thread.daemon = True
                server_thread.start()
                self.server_started = True
                return socket_path

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
                    with conn:
                        try:
                            data = conn.recv(1024)
                            if not data:
                                continue

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
                                print("Client disconnected, continuing...")
                                continue

                            # Log execution information
                            log_message = f"{func.__name__} called with args: {args}, kwargs: {kwargs}, time: {elapsed_time:.4f} seconds, lru_enabled: {self.lru_enabled}"
                            logger.debug(log_message)

                        except Exception as e:
                            logger.error(traceback.print_exc())
                            break

        return wrapper


def call_function(socket_path, args, kwargs):
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.connect(socket_path)
            s.sendall(json.dumps({"args": args, "kwargs": kwargs}).encode("utf-8"))

            data = s.recv(1024)
            if not data: return None
            json_data = json.loads(data.decode("utf-8"))
            return json_data.get("result", None)
    except Exception:
        print(traceback.print_exc())
        raise
