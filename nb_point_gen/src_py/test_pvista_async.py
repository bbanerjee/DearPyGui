import dearpygui.dearpygui as dpg
import numpy as np
from pathlib import Path
import struct
import random
from typing import List, Tuple, Optional
import pyvista as pv
import threading
import time
import queue
from dataclasses import dataclass
from enum import Enum
from pyvista_imgui import ImguiPlotter

import os
import sys

lib_dir = os.path.join("..", "build", "python_lib")
sys.path.append(lib_dir)

try:
    from point_generator_cpp import PointGenerator as PointGenerator
except ImportError as e:
    print(f"Error importing point_generator_cpp: {e}")
    sys.exit(1)

class MessageType(Enum):
    UPDATE_MESH = "update_mesh"
    UPDATE_POINTS = "update_points"
    CLEAR_POINTS = "clear_points"
    RESET_CAMERA = "reset_camera"
    CLOSE_VIEWER = "close_viewer"
    SET_WIREFRAME = "set_wireframe"
    SET_POINTS_VISIBLE = "set_points_visible"

@dataclass
class ViewerMessage:
    msg_type: MessageType
    data: any = None

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
        
        return np.array(vertices, dtype=np.float64, order='F'), np.array(faces, dtype=np.int32, order='F')
    
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

class AsyncPyVistaViewer:
    """Asynchronous 3D visualization using PyVista"""
    
    def __init__(self):
        self.message_queue = queue.Queue()
        self.viewer_thread = None
        self.plotter = None
        self.mesh_actor = None
        self.points_actor = None
        self.running = False
        self.show_wireframe = True
        self.show_points = True
        
    def start_viewer(self):
        """Start the PyVista viewer in a separate thread"""
        if self.viewer_thread is None or not self.viewer_thread.is_alive():
            self.running = True
            self.viewer_thread = threading.Thread(target=self._run_viewer, daemon=False)
            self.viewer_thread.start()
    
    def send_message(self, message: ViewerMessage):
        """Send a message to the viewer thread"""
        self.message_queue.put(message)
    
    def _run_viewer(self):
        """Run the PyVista plotter in its own thread"""
        try:
            # Initialize plotter
            #self.plotter = pv.Plotter(window_size=(1000, 700), title="CAD 3D Viewer")
            self.plotter = ImguiPlotter(window_size=(1000, 700), title="CAD 3D Viewer")
            self.plotter.add_text("Load an STL file to begin", position='upper_left', font_size=12)
            self.plotter.view_isometric()
            self.plotter.add_axes()
            
            # Set up background processing
            # self.plotter.add_timer_callback(self._process_messages, 50)  # Check every 50ms
            # self.plotter.add_timer_event(10000, 50, self._process_messages)
            
            # Show the plotter (non-blocking in this context)
            self.plotter.add_key_event('space', self._process_messages)
            self.plotter.show(auto_close=False)
            
        except Exception as e:
            print(f"PyVista viewer error: {e}")
        finally:
            self.running = False
    
    def _process_messages(self):
        """Process messages from the main thread"""
        try:
            # Process all pending messages
            while not self.message_queue.empty():
                try:
                    message = self.message_queue.get_nowait()
                    self._handle_message(message)
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Error processing messages: {e}")
    
    def _handle_message(self, message: ViewerMessage):
        """Handle a specific message"""
        try:
            if message.msg_type == MessageType.UPDATE_MESH:
                self._update_mesh(message.data['vertices'], message.data['faces'])
            elif message.msg_type == MessageType.UPDATE_POINTS:
                self._update_points(message.data)
            elif message.msg_type == MessageType.CLEAR_POINTS:
                self._clear_points()
            elif message.msg_type == MessageType.RESET_CAMERA:
                self._reset_camera()
            elif message.msg_type == MessageType.SET_WIREFRAME:
                self.show_wireframe = message.data
                self._refresh_mesh()
            elif message.msg_type == MessageType.SET_POINTS_VISIBLE:
                self.show_points = message.data
                self._refresh_points()
            elif message.msg_type == MessageType.CLOSE_VIEWER:
                if self.plotter:
                    self.plotter.close()
                self.running = False
        except Exception as e:
            print(f"Error handling message {message.msg_type}: {e}")
    
    def _update_mesh(self, vertices: np.ndarray, faces: np.ndarray):
        """Update the mesh visualization"""
        if not self.plotter:
            return
        
        # Remove existing mesh
        if self.mesh_actor is not None:
            self.plotter.remove_actor(self.mesh_actor)
            self.mesh_actor = None
        
        if len(vertices) > 0 and len(faces) > 0:
            # Create PyVista mesh
            pv_faces = []
            for face in faces:
                pv_faces.extend([3, face[0], face[1], face[2]])
            
            mesh = pv.PolyData(vertices, np.array(pv_faces))
            
            # Add mesh with current settings
            self.mesh_actor = self.plotter.add_mesh(
                mesh, 
                color='lightblue', 
                show_edges=self.show_wireframe,
                edge_color='navy',
                opacity=0.7,
                name='mesh'
            )
            
            # Fit camera to mesh
            self.plotter.reset_camera()
            self.plotter.render()
    
    def _update_points(self, points: np.ndarray):
        """Update the interior points visualization"""
        if not self.plotter:
            return
        
        # Remove existing points
        self._clear_points()
        
        if len(points) > 0 and self.show_points:
            # Create point cloud
            point_cloud = pv.PolyData(points)
            
            # Add points as spheres
            self.points_actor = self.plotter.add_mesh(
                point_cloud,
                color='red',
                point_size=8,
                render_points_as_spheres=True,
                name='interior_points'
            )
            
            self.plotter.render()
    
    def _clear_points(self):
        """Clear interior points"""
        if self.points_actor is not None and self.plotter:
            self.plotter.remove_actor(self.points_actor)
            self.points_actor = None
            self.plotter.render()
    
    def _reset_camera(self):
        """Reset camera view"""
        if self.plotter:
            self.plotter.reset_camera()
            self.plotter.view_isometric()
            self.plotter.render()
    
    def _refresh_mesh(self):
        """Refresh mesh with current settings"""
        if self.mesh_actor and self.plotter:
            mesh = self.mesh_actor.GetMapper().GetInput()
            self.plotter.remove_actor(self.mesh_actor)
            
            self.mesh_actor = self.plotter.add_mesh(
                mesh, 
                color='lightblue', 
                show_edges=self.show_wireframe,
                edge_color='navy',
                opacity=0.7,
                name='mesh'
            )
            self.plotter.render()
    
    def _refresh_points(self):
        """Refresh points visibility"""
        if not self.show_points and self.points_actor:
            self._clear_points()
    
    def is_running(self):
        """Check if viewer is running"""
        return self.running
    
    def close(self):
        """Close the viewer"""
        self.send_message(ViewerMessage(MessageType.CLOSE_VIEWER))
        if self.viewer_thread and self.viewer_thread.is_alive():
            self.viewer_thread.join(timeout=2.0)

class CADApplication:
    def __init__(self):
        self.vertices = np.array([])
        self.faces = np.array([])
        self.interior_points = np.array([])
        self.filename = ""
        self.viewer = AsyncPyVistaViewer()
        self.point_generation_thread = None
        self.is_generating_points = False
        
        # Setup DearPyGui
        dpg.create_context()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        with dpg.window(label="CAD STL Viewer - Controls", width=450, height=600, tag="main_window"):
            
            # 3D Viewer controls
            with dpg.group():
                dpg.add_text("3D Visualization", color=(255, 255, 0))
                with dpg.group(horizontal=True):
                    dpg.add_button(label="Open 3D Viewer", callback=self.open_3d_viewer)
                    dpg.add_button(label="Close 3D Viewer", callback=self.close_3d_viewer)
                dpg.add_text("Status: 3D viewer not started", tag="viewer_status")
            
            dpg.add_separator()
            
            # File operations
            with dpg.group():
                dpg.add_text("File Operations", color=(255, 255, 0))
                dpg.add_button(label="Load STL File", callback=self.show_file_dialog, width=200)
                dpg.add_text("No file loaded", tag="file_status", wrap=400)
            
            dpg.add_separator()
            
            # Point generation controls
            with dpg.group():
                dpg.add_text("Point Generation", color=(255, 255, 0))
                with dpg.group(horizontal=True):
                    dpg.add_text("Number of points:")
                    dpg.add_input_int(tag="num_points", default_value=100, min_value=1, max_value=10000, width=100)
                
                with dpg.group(horizontal=True):
                    dpg.add_button(label="Generate Interior Points", callback=self.generate_points, tag="generate_btn")
                    dpg.add_button(label="Clear Points", callback=self.clear_points)
                
                dpg.add_progress_bar(tag="progress_bar", default_value=0.0, overlay="Ready", width=400)
            
            dpg.add_separator()
            
            # Visualization controls
            with dpg.group():
                dpg.add_text("Visualization Options", color=(255, 255, 0))
                dpg.add_checkbox(label="Show Mesh Wireframe", default_value=True, 
                               tag="show_wireframe", callback=self.toggle_wireframe)
                dpg.add_checkbox(label="Show Interior Points", default_value=True, 
                               tag="show_points", callback=self.toggle_points)
                dpg.add_button(label="Reset Camera View", callback=self.reset_camera)
            
            dpg.add_separator()
            
            # Info display
            with dpg.group():
                dpg.add_text("Information", color=(255, 255, 0))
                dpg.add_text("Mesh Info: No mesh loaded", tag="mesh_info", wrap=400)
                dpg.add_text("Points Info: No points generated", tag="points_info", wrap=400)
            
            dpg.add_separator()
            
            # Instructions
            with dpg.group():
                dpg.add_text("Instructions:", color=(0, 255, 0))
                dpg.add_text("1. Click 'Open 3D Viewer' to start visualization", wrap=400)
                dpg.add_text("2. Load an STL file using 'Load STL File'", wrap=400)
                dpg.add_text("3. Set number of points and click 'Generate Interior Points'", wrap=400)
                dpg.add_text("4. 3D Viewer Controls:", wrap=400)
                dpg.add_text("   • Left Mouse: Rotate view", wrap=400)
                dpg.add_text("   • Mouse Wheel: Zoom in/out", wrap=400)
                dpg.add_text("   • Right Mouse: Pan view", wrap=400)
        
        # File dialog
        with dpg.file_dialog(directory_selector=False, show=False, callback=self.load_stl_file,
                           file_count=1, tag="file_dialog", width=700, height=400):
            dpg.add_file_extension(".stl", color=(255, 255, 0, 255))
    
    def open_3d_viewer(self):
        """Open the 3D viewer window"""
        if not self.viewer.is_running():
            self.viewer.start_viewer()
            dpg.set_value("viewer_status", "Status: 3D viewer starting...")
            
            # Give viewer time to initialize, then update status
            def update_status():
                time.sleep(2)
                if self.viewer.is_running():
                    dpg.set_value("viewer_status", "Status: 3D viewer running")
                    # Update with current data if available
                    if len(self.vertices) > 0:
                        self.update_3d_visualization()
                else:
                    dpg.set_value("viewer_status", "Status: Failed to start 3D viewer")
            
            threading.Thread(target=update_status, daemon=True).start()
        else:
            dpg.set_value("viewer_status", "Status: 3D viewer already running")
    
    def close_3d_viewer(self):
        """Close the 3D viewer window"""
        self.viewer.close()
        dpg.set_value("viewer_status", "Status: 3D viewer closed")
    
    def show_file_dialog(self):
        """Show file selection dialog"""
        dpg.show_item("file_dialog")
    
    def load_stl_file(self, sender, app_data):
        """Load STL file"""
        try:
            file_path = list(app_data['selections'].values())[0]
            self.filename = Path(file_path).name
            
            dpg.set_value("file_status", f"Loading: {self.filename}...")
            
            # Load file in background thread
            def load_in_background():
                try:
                    # Read STL file
                    self.vertices, self.faces = STLReader.read_stl(file_path)
                    
                    # Update UI from main thread context
                    dpg.set_value("file_status", f"Loaded: {self.filename}")
                    self.update_mesh_info()
                    
                    # Clear previous points
                    self.interior_points = np.array([])
                    self.update_points_info()
                    
                    # Update 3D visualization
                    self.update_3d_visualization()
                    
                except Exception as e:
                    dpg.set_value("file_status", f"Error loading {self.filename}: {str(e)}")
            
            threading.Thread(target=load_in_background, daemon=True).start()
            
        except Exception as e:
            dpg.set_value("file_status", f"Error: {str(e)}")
    
    def generate_points(self):
        """Generate interior points"""
        if len(self.vertices) == 0:
            dpg.set_value("points_info", "Load a mesh first!")
            return
        
        if self.is_generating_points:
            return
        
        try:
            num_points = dpg.get_value("num_points")
            self.is_generating_points = True
            dpg.configure_item("generate_btn", enabled=False)
            dpg.set_value("progress_bar", 0.0)
            dpg.configure_item("progress_bar", overlay="Generating points...")
            
            def progress_callback(current, total):
                progress = current / total
                dpg.set_value("progress_bar", progress)
                dpg.configure_item("progress_bar", overlay=f"Generated {current}/{total} points")
            
            # Generate points in background thread
            def generate_in_background():
                try:
                    self.interior_points = PointGenerator.generate_interior_points(
                        self.vertices, self.faces, num_points, progress_callback
                    )
                    
                    # Update UI
                    dpg.set_value("progress_bar", 1.0)
                    dpg.configure_item("progress_bar", overlay=f"Completed: {len(self.interior_points)} points")
                    self.update_points_info()
                    self.update_3d_visualization()
                    
                except Exception as e:
                    dpg.set_value("points_info", f"Error generating points: {str(e)}")
                    dpg.configure_item("progress_bar", overlay="Error occurred")
                finally:
                    self.is_generating_points = False
                    dpg.configure_item("generate_btn", enabled=True)
            
            self.point_generation_thread = threading.Thread(target=generate_in_background, daemon=True)
            self.point_generation_thread.start()
            
        except Exception as e:
            dpg.set_value("points_info", f"Error: {str(e)}")
            self.is_generating_points = False
            dpg.configure_item("generate_btn", enabled=True)
    
    def clear_points(self):
        """Clear interior points"""
        self.interior_points = np.array([])
        self.update_points_info()
        self.viewer.send_message(ViewerMessage(MessageType.CLEAR_POINTS))
        dpg.set_value("progress_bar", 0.0)
        dpg.configure_item("progress_bar", overlay="Ready")
    
    def toggle_wireframe(self):
        """Toggle wireframe display"""
        show_wireframe = dpg.get_value("show_wireframe")
        self.viewer.send_message(ViewerMessage(MessageType.SET_WIREFRAME, show_wireframe))
    
    def toggle_points(self):
        """Toggle points display"""
        show_points = dpg.get_value("show_points")
        self.viewer.send_message(ViewerMessage(MessageType.SET_POINTS_VISIBLE, show_points))
        if show_points and len(self.interior_points) > 0:
            self.viewer.send_message(ViewerMessage(MessageType.UPDATE_POINTS, self.interior_points))
    
    def reset_camera(self):
        """Reset camera view in 3D viewer"""
        self.viewer.send_message(ViewerMessage(MessageType.RESET_CAMERA))
    
    def update_mesh_info(self):
        """Update mesh information display"""
        info = f"Mesh Info: Vertices: {len(self.vertices)}, Faces: {len(self.faces)}"
        if len(self.vertices) > 0:
            bounds = np.max(self.vertices, axis=0) - np.min(self.vertices, axis=0)
            info += f"\nBounds: {bounds[0]:.2f} x {bounds[1]:.2f} x {bounds[2]:.2f}"
        dpg.set_value("mesh_info", info)
    
    def update_points_info(self):
        """Update points information display"""
        if len(self.interior_points) > 0:
            info = f"Points Info: Generated {len(self.interior_points)} interior points"
        else:
            info = "Points Info: No interior points generated"
        dpg.set_value("points_info", info)
    
    def update_3d_visualization(self):
        """Update the 3D visualization"""
        if self.viewer.is_running():
            # Update mesh
            if len(self.vertices) > 0:
                self.viewer.send_message(ViewerMessage(
                    MessageType.UPDATE_MESH, 
                    {'vertices': self.vertices, 'faces': self.faces}
                ))
            
            # Update points
            if len(self.interior_points) > 0:
                self.viewer.send_message(ViewerMessage(MessageType.UPDATE_POINTS, self.interior_points))
    
    def run(self):
        """Run the application"""
        dpg.create_viewport(title="CAD STL Viewer", width=500, height=650)
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