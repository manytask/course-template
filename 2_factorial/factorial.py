def factorial(n: int) -> int:
    """
    Calculate the factorial of a number.
    """
    # SOLUTION BEGIN
    if n == 0:
        return 1
    else:
        return n * factorial(n - 1)
    # SOLUTION END
