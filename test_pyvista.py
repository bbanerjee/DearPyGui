import dearpygui.dearpygui as dpg
import numpy as np
from pathlib import Path
import struct
import random
from typing import List, Tuple, Optional
import pyvista as pv
import threading
import time
from pyvista_imgui import ImguiPlotter

class STLReader:
    """Simple STL file reader supporting both ASCII and binary formats"""
    
    @staticmethod
    def read_stl(filename: str) -> Tuple[np.ndarray, np.ndarray]:
        """Read STL file and return vertices and faces"""
        with open(filename, 'rb') as f:
            # Check if binary or ASCII
            header = f.read(80)
            if b'solid' in header[:5].lower():
                f.seek(0)
                return STLReader._read_ascii_stl(f)
            else:
                return STLReader._read_binary_stl(f)
    
    @staticmethod
    def _read_binary_stl(f) -> Tuple[np.ndarray, np.ndarray]:
        """Read binary STL format"""
        f.seek(80)  # Skip header
        num_triangles = struct.unpack('<I', f.read(4))[0]
        
        vertices = []
        faces = []
        vertex_map = {}
        vertex_count = 0
        
        for i in range(num_triangles):
            # Skip normal vector (3 floats)
            f.read(12)
            
            # Read 3 vertices
            triangle_vertices = []
            for j in range(3):
                x, y, z = struct.unpack('<fff', f.read(12))
                vertex = (x, y, z)
                
                if vertex not in vertex_map:
                    vertex_map[vertex] = vertex_count
                    vertices.append(vertex)
                    vertex_count += 1
                
                triangle_vertices.append(vertex_map[vertex])
            
            faces.append(triangle_vertices)
            f.read(2)  # Skip attribute byte count
        
        return np.array(vertices), np.array(faces)
    
    @staticmethod
    def _read_ascii_stl(f) -> Tuple[np.ndarray, np.ndarray]:
        """Read ASCII STL format"""
        vertices = []
        faces = []
        vertex_map = {}
        vertex_count = 0
        
        lines = f.read().decode('utf-8').split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip().lower()
            if line.startswith('facet normal'):
                i += 2  # Skip to first vertex
                triangle_vertices = []
                
                # Read 3 vertices
                for j in range(3):
                    if i < len(lines):
                        vertex_line = lines[i].strip()
                        if vertex_line.startswith('vertex'):
                            coords = vertex_line.split()[1:4]
                            vertex = (float(coords[0]), float(coords[1]), float(coords[2]))
                            
                            if vertex not in vertex_map:
                                vertex_map[vertex] = vertex_count
                                vertices.append(vertex)
                                vertex_count += 1
                            
                            triangle_vertices.append(vertex_map[vertex])
                    i += 1
                
                if len(triangle_vertices) == 3:
                    faces.append(triangle_vertices)
                i += 1  # Skip 'endfacet'
            else:
                i += 1
        
        return np.array(vertices), np.array(faces)

class PointGenerator:
    """Generate points inside a triangulated surface"""
    
    @staticmethod
    def point_in_triangle(p1: np.ndarray, p2: np.ndarray, p3: np.ndarray) -> np.ndarray:
        """Generate random point inside triangle using barycentric coordinates"""
        r1, r2 = random.random(), random.random()
        if r1 + r2 > 1:
            r1, r2 = 1 - r1, 1 - r2
        r3 = 1 - r1 - r2
        return r1 * p1 + r2 * p2 + r3 * p3
    
    @staticmethod
    def is_point_inside_mesh(point: np.ndarray, vertices: np.ndarray, faces: np.ndarray) -> bool:
        """Ray casting algorithm to check if point is inside mesh"""
        ray_dir = np.array([1.0, 0.0, 0.0])  # Cast ray in X direction
        intersections = 0
        
        for face in faces:
            v0, v1, v2 = vertices[face]
            
            # Ray-triangle intersection using Möller-Trumbore algorithm
            edge1 = v1 - v0
            edge2 = v2 - v0
            h = np.cross(ray_dir, edge2)
            a = np.dot(edge1, h)
            
            if abs(a) < 1e-8:
                continue
            
            f = 1.0 / a
            s = point - v0
            u = f * np.dot(s, h)
            
            if u < 0.0 or u > 1.0:
                continue
            
            q = np.cross(s, edge1)
            v = f * np.dot(ray_dir, q)
            
            if v < 0.0 or u + v > 1.0:
                continue
            
            t = f * np.dot(edge2, q)
            
            if t > 1e-8:  # Ray intersects triangle
                intersections += 1
        
        return intersections % 2 == 1
    
    @staticmethod
    def generate_interior_points(vertices: np.ndarray, faces: np.ndarray, num_points: int) -> np.ndarray:
        """Generate points inside the mesh using rejection sampling"""
        if len(vertices) == 0:
            return np.array([])
        
        # Get bounding box
        min_bounds = np.min(vertices, axis=0)
        max_bounds = np.max(vertices, axis=0)
        
        interior_points = []
        attempts = 0
        max_attempts = num_points * 100  # Prevent infinite loops
        
        while len(interior_points) < num_points and attempts < max_attempts:
            # Generate random point in bounding box
            point = np.random.uniform(min_bounds, max_bounds)
            
            if PointGenerator.is_point_inside_mesh(point, vertices, faces):
                interior_points.append(point)
            
            attempts += 1
        
        return np.array(interior_points)

class PyVistaViewer:
    """3D visualization using PyVista"""
    
    def __init__(self):
        self.plotter = None
        self.mesh_actor = None
        self.points_actor = None
        self.viewer_thread = None
        self.should_close = False
        
    def start_viewer(self):
        """Start the PyVista viewer in a separate thread"""
        if self.viewer_thread is None or not self.viewer_thread.is_alive():
            self.should_close = False
            self.viewer_thread = threading.Thread(target=self._run_viewer, daemon=True)
            self.viewer_thread.start()
    
    def _run_viewer(self):
        """Run the PyVista plotter"""
        try:
            #self.plotter = pv.Plotter(window_size=(800, 600), title="CAD 3D Viewer")
            self.plotter = ImguiPlotter(window_size=(800, 600), title="CAD 3D Viewer")
            self.plotter.add_text("Load an STL file to begin", position='upper_left', font_size=12)
            
            # Set up a nice viewing angle
            self.plotter.view_isometric()
            self.plotter.add_axes()
            
            # Show the plotter (this blocks until window is closed)
            self.plotter.show()
            
        except Exception as e:
            print(f"PyVista viewer error: {e}")
    
    def update_mesh(self, vertices: np.ndarray, faces: np.ndarray):
        """Update the mesh visualization"""
        if self.plotter is None:
            return
        
        try:
            # Remove existing mesh
            if self.mesh_actor is not None:
                self.plotter.remove_actor(self.mesh_actor)
            
            if len(vertices) > 0 and len(faces) > 0:
                # Create PyVista mesh
                # Convert faces to PyVista format (prepend triangle count)
                pv_faces = []
                for face in faces:
                    pv_faces.extend([3, face[0], face[1], face[2]])
                
                mesh = pv.PolyData(vertices, np.array(pv_faces))
                
                # Add mesh with wireframe and surface
                self.mesh_actor = self.plotter.add_mesh(
                    mesh, 
                    color='lightblue', 
                    show_edges=True,
                    edge_color='navy',
                    opacity=0.7,
                    name='mesh'
                )
                
                # Fit camera to mesh
                self.plotter.reset_camera()
                
        except Exception as e:
            print(f"Error updating mesh: {e}")
    
    def update_points(self, points: np.ndarray):
        """Update the interior points visualization"""
        if self.plotter is None:
            return
        
        try:
            # Remove existing points
            if self.points_actor is not None:
                self.plotter.remove_actor(self.points_actor)
                self.points_actor = None
            
            if len(points) > 0:
                # Create point cloud
                point_cloud = pv.PolyData(points)
                
                # Add points as spheres
                self.points_actor = self.plotter.add_mesh(
                    point_cloud,
                    color='red',
                    point_size=5,
                    render_points_as_spheres=True,
                    name='interior_points'
                )
                
        except Exception as e:
            print(f"Error updating points: {e}")
    
    def close(self):
        """Close the viewer"""
        if self.plotter is not None:
            try:
                self.plotter.close()
            except:
                pass
        self.should_close = True

class CADApplication:
    def __init__(self):
        self.vertices = np.array([])
        self.faces = np.array([])
        self.interior_points = np.array([])
        self.filename = ""
        self.viewer = PyVistaViewer()
        
        # Setup DearPyGui
        dpg.create_context()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        with dpg.window(label="CAD STL Viewer - Controls", width=400, height=500, tag="main_window"):
            
            # 3D Viewer controls
            with dpg.group():
                dpg.add_text("3D Visualization")
                dpg.add_button(label="Open 3D Viewer", callback=self.open_3d_viewer)
                dpg.add_text("Status: 3D viewer not started", tag="viewer_status")
            
            dpg.add_separator()
            
            # File operations
            with dpg.group():
                dpg.add_text("File Operations")
                dpg.add_button(label="Load STL File", callback=self.show_file_dialog)
                dpg.add_text("No file loaded", tag="file_status")
            
            dpg.add_separator()
            
            # Point generation controls
            with dpg.group():
                dpg.add_text("Point Generation")
                with dpg.group(horizontal=True):
                    dpg.add_text("Number of points:")
                    dpg.add_input_int(tag="num_points", default_value=100, min_value=1, max_value=10000, width=100)
                dpg.add_button(label="Generate Interior Points", callback=self.generate_points)
                dpg.add_button(label="Clear Points", callback=self.clear_points)
            
            dpg.add_separator()
            
            # Visualization controls
            with dpg.group():
                dpg.add_text("Visualization Options")
                dpg.add_checkbox(label="Show Mesh Wireframe", default_value=True, tag="show_wireframe")
                dpg.add_checkbox(label="Show Interior Points", default_value=True, tag="show_points")
                dpg.add_button(label="Reset Camera View", callback=self.reset_camera)
            
            dpg.add_separator()
            
            # Info display
            with dpg.group():
                dpg.add_text("Information")
                dpg.add_text("Mesh Info:", tag="mesh_info")
                dpg.add_text("Points Info:", tag="points_info")
            
            dpg.add_separator()
            
            # Instructions
            with dpg.group():
                dpg.add_text("Instructions:")
                dpg.add_text("1. Click 'Open 3D Viewer' to start visualization")
                dpg.add_text("2. Load an STL file")
                dpg.add_text("3. Generate interior points")
                dpg.add_text("4. Interact with 3D viewer:")
                dpg.add_text("   - Mouse: Rotate view")
                dpg.add_text("   - Scroll: Zoom")
                dpg.add_text("   - Right-click: Pan")
        
        # File dialog
        with dpg.file_dialog(directory_selector=False, show=False, callback=self.load_stl_file,
                           file_count=1, tag="file_dialog", width=700, height=400):
            dpg.add_file_extension(".stl", color=(255, 255, 0, 255))
    
    def open_3d_viewer(self):
        """Open the 3D viewer window"""
        self.viewer.start_viewer()
        dpg.set_value("viewer_status", "Status: 3D viewer started")
        time.sleep(1)  # Give viewer time to initialize
        
        # Update with current data if available
        if len(self.vertices) > 0:
            self.update_3d_visualization()
    
    def show_file_dialog(self):
        """Show file selection dialog"""
        dpg.show_item("file_dialog")
    
    def load_stl_file(self, sender, app_data):
        """Load STL file"""
        try:
            file_path = list(app_data['selections'].values())[0]
            self.filename = Path(file_path).name
            
            # Read STL file
            self.vertices, self.faces = STLReader.read_stl(file_path)
            
            # Update UI
            dpg.set_value("file_status", f"Loaded: {self.filename}")
            self.update_mesh_info()
            
            # Clear previous points
            self.interior_points = np.array([])
            self.update_points_info()
            
            # Update 3D visualization
            self.update_3d_visualization()
            
        except Exception as e:
            dpg.set_value("file_status", f"Error: {str(e)}")
    
    def generate_points(self):
        """Generate interior points"""
        if len(self.vertices) == 0:
            dpg.set_value("points_info", "Load a mesh first!")
            return
        
        try:
            num_points = dpg.get_value("num_points")
            dpg.set_value("points_info", "Generating points... (this may take a moment)")
            
            # Generate points in a separate thread to avoid blocking UI
            def generate_in_background():
                self.interior_points = PointGenerator.generate_interior_points(
                    self.vertices, self.faces, num_points
                )
                # Update UI from main thread
                dpg.set_value("points_info", f"Generated {len(self.interior_points)} interior points")
                self.update_3d_visualization()
            
            threading.Thread(target=generate_in_background, daemon=True).start()
            
        except Exception as e:
            dpg.set_value("points_info", f"Error generating points: {str(e)}")
    
    def clear_points(self):
        """Clear interior points"""
        self.interior_points = np.array([])
        self.update_points_info()
        self.update_3d_visualization()
    
    def reset_camera(self):
        """Reset camera view in 3D viewer"""
        if self.viewer.plotter is not None:
            self.viewer.plotter.reset_camera()
            self.viewer.plotter.view_isometric()
    
    def update_mesh_info(self):
        """Update mesh information display"""
        info = f"Vertices: {len(self.vertices)}, Faces: {len(self.faces)}"
        if len(self.vertices) > 0:
            bounds = np.max(self.vertices, axis=0) - np.min(self.vertices, axis=0)
            info += f"\nBounds: {bounds[0]:.2f} x {bounds[1]:.2f} x {bounds[2]:.2f}"
        dpg.set_value("mesh_info", info)
    
    def update_points_info(self):
        """Update points information display"""
        if len(self.interior_points) > 0:
            info = f"Interior points: {len(self.interior_points)}"
        else:
            info = "No interior points generated"
        dpg.set_value("points_info", info)
    
    def update_3d_visualization(self):
        """Update the 3D visualization"""
        # Update mesh
        self.viewer.update_mesh(self.vertices, self.faces)
        
        # Update points
        if dpg.get_value("show_points") if dpg.does_item_exist("show_points") else True:
            self.viewer.update_points(self.interior_points)
        else:
            self.viewer.update_points(np.array([]))
    
    def run(self):
        """Run the application"""
        dpg.create_viewport(title="CAD STL Viewer", width=450, height=600)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("main_window", True)
        
        try:
            dpg.start_dearpygui()
        finally:
            self.viewer.close()
            dpg.destroy_context()

if __name__ == "__main__":
    app = CADApplication()
    app.run()