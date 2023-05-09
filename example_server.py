#!/usr/bin/env python

import time
import logging
import lip as lip


@lip.LIPModule(lru=True, log_level=logging.DEBUG)
def cpu_intensive_sum_of_squares(n):
    """
    This function calculates the sum of squares from 1 to n.

    :param n: The number to calculate the sum of squares up to.
    :return: The sum of squares from 1 to n.
    """
    total = 0
    for i in range(1, n + 1):
        total += i * i
    return total


@lip.LIPModule(lru=True)
def add_ints(*a):
    """
    This function adds a list of integers.

    :param a: A list of integers.
    :return: The sum of the integers.
    """
    return sum(a)


if __name__ == '__main__':
    try:
        # Initialize the functions
        print("Initializing functions...")
        
        # - Add ints together
        s_add_ints = add_ints(init=True)
        print(f"add_ints: {s_add_ints}")

        # - Calculate the sum of squares
        s_cpu_intensive_sum_of_squares = cpu_intensive_sum_of_squares(init=True)
        print(f"cpu_intensive_sum_of_squares: {s_cpu_intensive_sum_of_squares}")
        
        print("Server running...")

        # Do some work after the threads are running... 
        for x in range(120):
            print(f"\r\033[KCounting 120 sheep...{x} Then ending the server", end="", flush=True)
            time.sleep(1)

    except Exception as e:
        print(e)
    finally:
        print("\nShutting down services...")
        s_add_ints.terminate()
        s_cpu_intensive_sum_of_squares.terminate()
        print("Done!")

