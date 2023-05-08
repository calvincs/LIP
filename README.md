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
import lip

@lip.LIPModule(log_level=logging.DEBUG, lru=True, lru_max=10)
def my_function(a, b):
    """This function adds two numbers."""
    return a + b

# Start the server
server = my_function(init=True)
```

### 2. Communicating with the server using LIPClient

To call the exposed functions and retrieve their results, create an instance of `LIPClient` and use its methods. Here's an example:

```python
client = lip.LIPClient()

# List available functions
print(client.list_functions())

# Get the docstring of a function
print(client.get_docstring("my_function"))

# Call a function and get the result
result = client.call_function("my_function", args=[2, 3])
print(result)
```

### 3. Server shutdown

To shut down the server gracefully, call the `terminate()` method on the `LIPModule` instance:

```python
server.terminate()
```

## Usage Examples

### Example 1: Basic usage

Here is an example of how to create a simple server that adds two numbers:

```python
import lip
import logging
import time

@lip.LIPModule(log_level=logging.DEBUG)
def add_two_numbers(a, b):
    """This function adds two numbers."""
    return a + b

if __name__ == '__main__':
    server = add_two_numbers(init=True)
    
    try:
        # Do other things
        time.sleep(20)
    finally:
        server.terminate()
```

And here's how to use `LIPClient` to interact with this server:

```python
import lip

client = lip.LIPClient()

# Call add_two_numbers function and print the result
result = client.call_function("add_two_numbers", args=[5, 7])
print(result)  # Output: 12
```

### Example 2: Using LRU caching

This example demonstrates how to enable LRU caching for a CPU-intensive function:

```python
import lip
import time

@lip.LIPModule(lru=True, lru_max=10)
def cpu_intensive_sum_of_squares(n):
    """This function calculates the sum of squares from 1 to n."""
    total = 0
    for i in range(1, n + 1):
        total += i * i
    return total

if __name__ == '__main__':
    server = cpu_intensive_sum_of_squares(init=True)
    
    try:
        # Do other things
        time.sleep(20)
    finally:
        server.terminate()
```

And here's how to use `LIPClient` to interact with this server:

```python
import lip

client = lip.LIPClient()

# Call cpu_intensive_sum_of_squares function and print the result
result = client.call_function("cpu_intensive_sum_of_squares", args=[5])
print(result)  # Output: 55
```

### Example 3: Logging and error handling

In this example, we will demonstrate how to enable logging and handle errors when using LIPModule and LIPClient:

```python
import lip
import logging

@lip.LIPModule(log_level=logging.DEBUG)
def divide_numbers(a, b):
    """This function divides two numbers."""
    if b == 0:
        raise ValueError("Division by zero is not allowed.")
    return a / b

if __name__ == '__main__':
    server = divide_numbers(init=True)
    
    try:
        # Do other things
        time.sleep(20)
    finally:
        server.terminate()
```

And here's how to use `LIPClient` to interact with this server and handle exceptions:

```python
import lip

client = lip.LIPClient()

try:
    # Call divide_numbers function with b=0 (raises an exception)
    result = client.call_function("divide_numbers", args=[10, 0])
except ValueError as e:
    print(f"Error: {e}")
```

This will output:

```
Error: Division by zero is not allowed.
```

## Important Notes

- Make sure the server is running before using the `LIPClient` methods to interact with it.
- When calling a function with `LIPClient`, provide the function name as a string, along with any required arguments and keyword arguments.
- If a function is not found or an error occurs during execution, an exception will be raised. Make sure to handle exceptions as needed.
- The `LIPClient` class provides a `refresh_sockets` method to rescan for available sockets. Call this method when you want to update the list of available functions.
- Ensure the `/tmp` directory is writable, as the codebase uses it to create Unix domain socket files.

## Author
 - Twitter - [Calvin Schultz](https://twitter.com/0000CCS)