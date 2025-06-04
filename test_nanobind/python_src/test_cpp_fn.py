import sys
import os

lib_dir = os.path.join("..", "build", "python_lib")
sys.path.append(lib_dir)

try:
    import test_cpp_lib
except ImportError as e:
    print(f"Error importing test_cpp_lib: {e}")
    sys.exit(1)

# Call the add_integers function
result_add = test_cpp_lib.add_integers(5, 3)
print(f"5 + 3 = {result_add}")

# Call the multiply_doubles function
result_multiply = test_cpp_lib.multiply_double(2.5, 4.0)
print(f"2.5 * 4.0 = {result_multiply}")

# Access docstrings
print(f"\nModule docstring: {test_cpp_lib.__doc__}")
print(f"add_integers docstring: {test_cpp_lib.add_integers.__doc__}")