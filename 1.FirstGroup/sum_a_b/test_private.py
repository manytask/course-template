import pytest

from sum_a_b import sum_a_b


@pytest.mark.parametrize(
    "a,b,expected",
    [
        (1.0, 2.0, 3.0),
        (1.1, 0.0, 1.1),
        (0.0001, 0.0001, 0.0002),
        (-1.0, 0.01, -0.99),
    ],
)
def test_sum_a_b_complex(a: float, b: float, expected: float) -> None:
    assert sum_a_b(a, b) == pytest.approx(expected)
