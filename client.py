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






from lip import LIPClient
import time

def main():
    try:
        lip = LIPClient()
        counter = 0

        # Print out the docstring
        documentation = lip.get_docstring("cpu_intensive_sum_of_squares")
        print(documentation)

        start_time = time.time()  # Record the start time
        for i in range(20000):
            lip.call_function("cpu_intensive_sum_of_squares", [i], {})
        end_time = time.time()  # Record the end time
        elapsed_time = end_time - start_time  # Calculate the time taken
        print(f"Total time: {elapsed_time:.4f} seconds")


        functions = lip.list_functions()
        print(functions)
    
    except Exception as e:
        print(e)

if __name__ == '__main__':
    main()