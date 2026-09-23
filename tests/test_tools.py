import pytest

from app.tools.registry import calculator


def test_calculator_valid_expression():
    assert calculator("(12/100)*45000")["result"] == 5400


def test_calculator_rejects_unsafe_expression():
    with pytest.raises(ValueError):
        calculator("__import__('os').system('echo unsafe')")
