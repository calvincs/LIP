#!venv/bin/python3

# # Imports
# import lipc_module as lipc
# import time
# import random

# def main():
#     try:
#         counter = 0
#         start_time = time.time()  # Record the start time

#         for i in range(20000):  

#             results = lipc.call_function("/tmp/lipcm-cpu_intensive_sum_of_squares.sock", [i], {})
#             print(results)

#         end_time = time.time()  # Record the end time
#         elapsed_time = end_time - start_time  # Calculate the time taken
#         print(f"Total time: {elapsed_time:.4f} seconds")

#     except Exception as e:
#         print(e)

# if __name__ == '__main__':
#     main()






from lipc_module import LIPCClient
import time

def main():
    try:
        lipc = LIPCClient()
        counter = 0
        start_time = time.time()  # Record the start time
        for i in range(20000):
            lipc.call_function("cpu_intensive_sum_of_squares", [i], {})
        end_time = time.time()  # Record the end time
        elapsed_time = end_time - start_time  # Calculate the time taken
        print(f"Total time: {elapsed_time:.4f} seconds")


        functions = lipc.list_functions()
        print(functions)
    
    except Exception as e:
        print(e)

if __name__ == '__main__':
    main()