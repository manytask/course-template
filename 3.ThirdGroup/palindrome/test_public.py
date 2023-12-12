from .palindrome import is_palindrome


def test_simple_palindrome():
    assert is_palindrome("radar")


def test_non_palindrome():
    assert not is_palindrome("hello")


def test_palindrome_with_spaces():
    assert is_palindrome("A man, a plan, a canal, Panama")


def test_palindrome_with_mixed_case():
    assert is_palindrome("RaceCar")


def test_empty_string():
    assert is_palindrome("")
