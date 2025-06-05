import sys
import os

import numpy as np

lib_dir = os.path.join("..", "build", "python_lib")
sys.path.append(lib_dir)

try:
    import point_generator_cpp
except ImportError as e:
    print(f"Error importing point_generator_cpp: {e}")
    sys.exit(1)

# 1. point_in_triangle
p1 = np.array([0.0, 0.0, 0.0], dtype=np.float64, order='C')
p2 = np.array([1.0, 0.0, 0.0], dtype=np.float64, order='C')
p3 = np.array([0.0, 1.0, 0.0], dtype=np.float64, order='C')
random_point_in_triangle = point_generator_cpp.PointGenerator.point_in_triangle(p1, p2, p3)
print(f"Random point in triangle: {random_point_in_triangle}")

# 2. is_point_inside_mesh
# Define a simple cube mesh
vertices = np.array([
    [0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 1.0, 0.0], [0.0, 1.0, 0.0],
    [0.0, 0.0, 1.0], [1.0, 0.0, 1.0], [1.0, 1.0, 1.0], [0.0, 1.0, 1.0]
], dtype=np.float64, order='F')

faces = np.array([
    [0, 1, 2], [0, 2, 3],  # Bottom face
    [4, 5, 6], [4, 6, 7],  # Top face
    [0, 4, 7], [0, 7, 3],  # Left face
    [1, 5, 6], [1, 6, 2],  # Right face
    [0, 1, 5], [0, 5, 4],  # Front face
    [3, 2, 6], [3, 6, 7]   # Back face
], dtype=np.int32, order='F')

point_inside = np.array([0.5, 0.5, 0.5], dtype=np.float64)
point_outside = np.array([2.0, 0.5, 0.5], dtype=np.float64)

print(f"Is point_inside inside mesh? {point_generator_cpp.PointGenerator.is_point_inside_mesh(point_inside, vertices, faces)}")
print(f"Is point_outside inside mesh? {point_generator_cpp.PointGenerator.is_point_inside_mesh(point_outside, vertices, faces)}")

# 3. generate_interior_points with progress callback
def my_progress_callback(current, total):
    print(f"Generated {current}/{total} points...")

num_points_to_generate = 50
print(f"\nGenerating {num_points_to_generate} interior points...")
interior_points = point_generator_cpp.PointGenerator.generate_interior_points(
    vertices, faces, num_points_to_generate, my_progress_callback
)
print(f"Generated {len(interior_points)} interior points.")
if len(interior_points) > 0:
    print(f"First 5 interior points:\n{interior_points[:5]}")