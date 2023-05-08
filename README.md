# LIPModule & LIPClient

## Overview

LIPModule and LIPClient provide a framework for creating and managing standalone Python modules that can be run as lightweight, Unix domain socket-based servers. The primary purpose of this codebase is to allow developers to create highly modular and scalable applications by enabling the separation of concerns, isolating module functionality, and reducing the overhead of deploying services.

## Who

Developers who want to create highly modular applications, split functionality into separate processes, and manage the execution of functions through Unix domain sockets can benefit from using this codebase.

## What

This codebase provides two classes:

1. `LIPModule`: A decorator that can be used to create standalone Python modules that act as lightweight servers. Functions decorated with `LIPModule` can be called via Unix domain sockets, enabling communication between different processes.

2. `LIPClient`: A client class that connects to LIPModule servers and provides an interface for calling the exposed functions and retrieving their results.

## Why

Using this codebase can help you achieve the following goals:

- Create highly modular applications by splitting functionality into separate processes.
- Reduce the overhead of deploying services by using lightweight Unix domain sockets for inter-process communication.
- Isolate module functionality, improving maintainability, and reducing potential bugs.
- Leverage built-in logging, caching, and error handling features.

## How to Use

### 1. Creating a server with LIPModule

To create a server, define a function and decorate it with `LIPModule`. You can customize the log level, caching, and other options by passing arguments to the decorator. Here's an example:

```python
@LIPModule(log_level=logging.DEBUG, lru=True, lru_max=10)
def my_function(a, b):
    """This function adds two numbers."""
    return a + b

# Start the server
my_function(init=True)
```

### 2. Communicating with the server using LIPClient

To call the exposed functions and retrieve their results, create an instance of `LIPClient` and use its methods. Here's an example:

```python
client = LIPClient()

# List available functions
print(client.list_functions())

# Get the docstring of a function
print(client.get_docstring("my_function"))

# Call a function and get the result
result = client.call_function("my_function", args=[2, 3])
print(result)
```

### 3. Server shutdown

To shut down the server gracefully, call the decorated function with the `exit=True` keyword argument:

```python
my_function(exit=True)
```

## Important Notes

- Make sure the server is running before using the `LIPClient` methods to interact with it.
- When calling a function with `LIPClient`, provide the function name as a string, along with any required arguments and keyword arguments.
- If a function is not found or an error occurs during execution, an exception will be raised. Make sure to handle exceptions as needed.
- The `LIPClient` class provides a `refresh_sockets` method to rescan for available sockets. Call this method when you want to update the list of available functions.
- Ensure the `/tmp` directory is writable, as the codebase uses it to create Unix domain socket files.