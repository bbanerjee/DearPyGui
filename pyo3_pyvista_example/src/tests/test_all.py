import pytest
import pyo3_pyvista_example


def test_sum_as_string():
    assert pyo3_pyvista_example.sum_as_string(1, 1) == "2"
