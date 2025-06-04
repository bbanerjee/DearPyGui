import numpy as np
import pyo3_pyvista_example as stl_reader

with open('binary_test.stl', 'wb') as f:
    f.write(b"HEADER" * 10)
    f.write(np.uint32(1).tobytes())
    f.write(np.float32([0.0, 0.0, 1.0]).tobytes())
    f.write(np.float32([0.0, 0.0, 0.0]).tobytes())
    f.write(np.float32([1.0, 0.0, 0.0]).tobytes())
    f.write(np.float32([0.0, 1.0, 0.0]).tobytes())
    f.write(b"\x00\x00")

with open('ascii_test.stl', 'w') as f:
    f.write("solid test_ascii_stl\n")
    f.write("  facet normal 0.0 0.0 1.0\n")
    f.write("     outer loop\n")
    f.write("        vertex 0.0 0.0 0.0\n")
    f.write("        vertex 1.0 0.0 0.0\n")
    f.write("        vertex 0.0 1.0 0.0\n")
    f.write("     endloop\n")
    f.write("  endface\n")
    f.write("endsolid test_ascii_stl\n")

reader = stl_reader.StlReader()

verts_b, faces_b = reader.read_stl("binary_test.stl")
print("Vertices = ", verts_b)

verts_a, faces_a = reader.read_stl("ascii_test.stl")
print("Vertices = ", verts_a)
