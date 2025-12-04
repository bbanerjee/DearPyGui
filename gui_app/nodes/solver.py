# nodes/solver.py
import dearpygui.dearpygui as dpg
import time
import threading
from nodes.base_node import BaseNode
from app import get_app_singleton

class SolverNode(BaseNode):
    def __init__(self):
        super().__init__(name="Solver")

        self.input_mesh = None
        self.results = None
        self.is_running = False

        # Clear placeholder and add real controls
        static_tag = f"{self.tag}_static"
        dpg.delete_item(static_tag, children_only=True)

        with dpg.node_attribute(parent=self.node_tag,
                               attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_text("Solver Settings", bullet=True)
            dpg.add_combo(label="Type", items=["Steady-State", "Transient"],
                          default_value="Steady-State", tag=f"{self.tag}_type",
                          width=100)
            dpg.add_slider_int(label="Max Iterations", default_value=1000,
                              min_value=10, max_value=10000, tag=f"{self.tag}_iters",
                              width=200)
            dpg.add_slider_float(label="Tolerance", default_value=1e-6,
                                min_value=1e-12, max_value=1.0, format="%.0e",
                                tag=f"{self.tag}_tol",
                                width=200)
            dpg.add_separator()
            dpg.add_button(label="Run Solver", callback=self.start_solver, width=200)
            dpg.add_progress_bar(tag=f"{self.tag}_progress", width=200, height=8)
            dpg.add_text("Ready", tag=f"{self.tag}_status")

    def set_input(self, attr_id, upstream_node):
        if hasattr(upstream_node, "output_mesh"):
            self.input_mesh = upstream_node.output_mesh
        elif hasattr(upstream_node, "ms") and upstream_node.ms:
            self.input_mesh = upstream_node.ms.current_mesh()
        dpg.set_value(f"{self.tag}_status", "Mesh received")

    def start_solver(self, sender=None, data=None):
        if self.is_running:
            return
        if self.input_mesh is None:
            dpg.set_value(f"{self.tag}_status", "Error: No input mesh")
            return

        self.is_running = True
        dpg.set_value(f"{self.tag}_status", "Running...")
        dpg.set_value(f"{self.tag}_progress", 0.0)

        # Run in background thread so GUI stays responsive
        thread = threading.Thread(target=self.run_solver, daemon=True)
        thread.start()

    def run_solver(self):
        import numpy as np
        max_iter = dpg.get_value(f"{self.tag}_iters")
        tol = dpg.get_value(f"{self.tag}_tol")

        # Fake solver loop (replace with OpenFOAM, CalculiX, SU2, etc.)
        for i in range(1, max_iter + 1):
            if not self.is_running:
                break
            time.sleep(0.02)  # simulate work
            progress = i / max_iter
            residual = tol * 10 * np.exp(-5 * progress)  # fake convergence

            dpg.configure_item(f"{self.tag}_progress", overlay=f"{i}/{max_iter}")
            dpg.set_value(f"{self.tag}_progress", progress)
            dpg.set_value(f"{self.tag}_status",
                         f"Iter {i} | Residual: {residual:.2e}")

            if residual < tol:
                break

        # Generate fake scalar field (pressure or temperature)
        verts = self.input_mesh.vertex_matrix()
        fake_field = np.sin(5 * verts[:, 0]) * np.cos(5 * verts[:, 1])

        self.results = {
            "pressure": fake_field,
            "converged": residual < tol,
            "iterations": i
        }

        # Visualize result
        get_app_singleton().viewer.load_mesh(self.input_mesh, scalar_field=fake_field,
                                  colormap=dpg.mvPlotColormap_Jet,
                                  scalar_range=[-1, 1])

        status = "Converged" if self.results["converged"] else "Max iterations reached"
        dpg.set_value(f"{self.tag}_status", f"Done: {status} ({i} iters)")
        dpg.set_item_label(self.node_tag, f"Solver: {status}")
        self.is_running = False

    def clear_input(self):
        self.input_mesh = None
        self.results = None
        self.is_running = False
        dpg.set_value(f"{self.tag}_status", "Ready")
        dpg.set_value(f"{self.tag}_progress", 0.0)