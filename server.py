#!venv/bin/python3

# import time
# import lipc_module as lipc

# @lipc.unix_socket_decorator()
# def add_two_ints(x, y):
#     for i in range(10):
#         print(f"Adding {x} and {y}...")
#         x += y
#     return x


# @lipc.unix_socket_decorator()
# def cpu_intensive_sum_of_squares(n):
#     total = 0
#     for i in range(1, n + 1):
#         total += i * i
#     return total

# if __name__ == '__main__':
#     print("Initializing functions...")
#     #socket_path = add_two_ints(init=True, debug=True)
#     socket_path = cpu_intensive_sum_of_squares(init=True, lru=True)
#     print("Server running...")

#     try:
#         while True:
#             time.sleep(5)
#     except KeyboardInterrupt:
#         print("Server shutting down...")
#         lipc.call_function("/tmp/python_add_two_ints.sock", [], {"exit": True})
import time
import lipc_module as lipc

lipc_module = lipc.LIPCModule()

@lipc_module
def add_two_ints(x, y):
    for i in range(10):
        print(f"Adding {x} and {y}...")
        x += y
    return x

@lipc_module
def cpu_intensive_sum_of_squares(n):
    total = 0
    for i in range(1, n + 1):
        total += i * i
    return total

if __name__ == '__main__':
    print("Initializing functions...")
    #socket_path = add_two_ints(init=True, debug=True)
    socket_path = cpu_intensive_sum_of_squares(init=True, lru=True)
    print("Server running...")

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        print("Server shutting down...")
        lipc.call_function("/tmp/python_add_two_ints.sock", [], {"exit": True})
