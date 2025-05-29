import numpy as np

import sys
print(sys.executable) # Make sure this is the Python you expect
print(sys.path) # Check if your project's build output or site-packages is listed

import rust_array_ext
print(rust_array_ext.__file__) # This will show you the exact path to the .so file being loaded.

try:
    import rust_array_ext
    print(dir(rust_array_ext))
except ImportError as e:
    print(f"Error importing rust_array_ext: {e}")
    raise

if __name__ == "__main__":
    a = np.array([1,2,3,4,5], dtype=np.int32)
    b = np.array([1,2,3,4,5], dtype=np.int32)
    res_rust = rust_array_ext.add_arrays(a, b)
    print(res_rust)