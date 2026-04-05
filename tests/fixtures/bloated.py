"""
Simple math utilities module.

This module provides basic mathematical operations that can be used
throughout the application. It includes functions for addition,
multiplication, factorial calculation, and prime number checking.
All functions are thoroughly documented and tested.
"""


def add(a: float, b: float) -> float:
    """
    Add two floating point numbers together and return their sum.

    This function accepts two numeric values and returns the result
    of adding them together. It handles both positive and negative
    numbers, as well as zero values correctly.

    Args:
        a: The first number to add to the second number.
        b: The second number to add to the first number.

    Returns:
        A float representing the sum of the two input numbers.
    """
    # Store the first input value in a clearly named local variable
    first_number = a
    # Store the second input value in a clearly named local variable
    second_number = b
    # Perform the addition operation by combining the two values
    result = first_number + second_number
    # Return the final computed result to the caller
    return result


def multiply(a: float, b: float) -> float:
    """
    Multiply two floating point numbers and return their product.

    This function takes two numeric inputs and returns the result
    of multiplying them together. Handles positive, negative, and
    zero values correctly per standard arithmetic rules.

    Args:
        a: The first operand (multiplicand).
        b: The second operand (multiplier).

    Returns:
        A float representing the product of the two input numbers.
    """
    # Assign first operand to a descriptive local variable
    first_operand = a
    # Assign second operand to a descriptive local variable
    second_operand = b
    # Compute the product of the two operands
    product = first_operand * second_operand
    # Return the computed product value
    return product


def factorial(n: int) -> int:
    """
    Calculate the factorial of a non-negative integer n.

    The factorial of n (written n!) is defined as the product of all
    positive integers from 1 to n. The factorial of 0 is defined as 1
    by convention.

    Args:
        n: A non-negative integer whose factorial is to be computed.

    Returns:
        The integer factorial of n.

    Raises:
        ValueError: If n is a negative integer.
    """
    # First validate that the input is non-negative
    if n < 0:
        raise ValueError("n must be non-negative")

    # Handle the special base case where n equals zero
    if n == 0:
        # The factorial of zero is defined as one by mathematical convention
        base_case_result = 1
        return base_case_result

    # Initialize the accumulator variable to store the running product
    result = 1
    # Define the start of the iteration range
    start_value = 1
    # Define the end of the iteration range (exclusive upper bound)
    end_value = n + 1

    # Iterate through each integer in the range and multiply into result
    for i in range(start_value, end_value):
        # Multiply the current accumulator by the loop variable
        result = result * i

    # Return the final computed factorial value
    return result


def is_prime(n: int) -> bool:
    """
    Determine whether a given integer is a prime number.

    A prime number is a natural number greater than 1 that has no
    positive divisors other than 1 and itself. This function uses
    trial division up to the square root of n for efficiency.

    Args:
        n: The integer to test for primality.

    Returns:
        True if n is prime, False otherwise.
    """
    # Numbers less than 2 are not considered prime by definition
    if n < 2:
        return False

    # Compute the integer square root to use as the upper bound
    square_root_value = int(n**0.5)
    # The upper limit for trial division is one past the square root
    upper_limit = square_root_value + 1

    # Try dividing n by each integer from 2 to the square root
    for i in range(2, upper_limit):
        # Compute the remainder to check divisibility
        remainder = n % i
        # If the remainder is zero, n is divisible and thus not prime
        if remainder == 0:
            return False

    # No divisor was found — n is prime
    return True
