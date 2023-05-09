#!/usr/bin/env python

import lip

# Instantiate LIPClient
client = lip.LIPClient()

# Call cpu_intensive_sum_of_squares function and print the result
result1 = client.call_function("cpu_intensive_sum_of_squares", args=[500])
print(f"Sum of squares up to 5: {result1}")  # Output: 41791750
print()

# Call add_ints function with a list of integers and print the result
result2 = client.call_function("add_ints", args=[1, 2, 3, 4, 5])
print(f"Sum of the list [1, 2, 3, 4, 5]: {result2}")  # Output: 15
print()

# List available functions
print("Available functions:")
for func in client.list_functions():
    print(f"- {func}")

print()

# Get the docstrings for both functions
doc1 = client.get_docstring("cpu_intensive_sum_of_squares")
doc2 = client.get_docstring("add_ints")
print("Function descriptions:")

print(f"cpu_intensive_sum_of_squares: {doc1}")
print()

print(f"add_ints: {doc2}")

# Refresh the list of available sockets (functions)
client.refresh_sockets()
