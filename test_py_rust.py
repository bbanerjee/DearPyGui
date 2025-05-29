import ctypes
import os

def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        a, b = 0, 1
        for _ in range(n - 1):
            a, b = b, a + b
        return b

_library_file = "librust_fib_lib.so"
library_path = os.path.join(os.path.dirname(__file__), 
                            'rust_fib_lib', 'target', 'release', _library_file)

try:
    rust_lib = ctypes.CDLL(library_path)
    rust_lib.fib_rs.argtypes = [ctypes.c_int]
    rust_lib.fib_rs.restype = ctypes.c_int

    def fib_from_rust(n):
        return rust_lib.fib_rs(n)

except OSError as e:
    print(f"Error loading Rust library: {e}")
    print(f"Please ensure '{_library_file}' is present in '{os.path.join('rust_fib_lib', 'target', 'release')}'")
    print("You might need to run `cargo build --release` inside the 'rust_fib_lib' directory.")
    exit(1)

if __name__ == "__main__":

    n_val = 10

    # Call python
    py_val = fibonacci(n_val)
    print(f"Fibonacci(10) (Python): {py_val}")

    # Call rust
    rs_val = fib_from_rust(n_val)
    print(f"Fibonacci(10) (Rust): {rs_val}")