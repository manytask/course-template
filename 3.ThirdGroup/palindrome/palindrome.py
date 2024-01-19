def is_palindrome(s: str) -> bool:
    """
    Check if a string is a palindrome.
    """
    # SOLUTION BEGIN
    cleaned_s = "".join(e for e in s if e.isalnum()).lower()
    return cleaned_s == cleaned_s[::-1]
    # SOLUTION END
