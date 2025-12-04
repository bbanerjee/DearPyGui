# nodes/post_process.py
import dearpygui.dearpygui as dpg
import numpy as np
from nodes.base_node import BaseNode
from app import get_app_singleton

class PostProcessNode(BaseNode):
    def __init__(self):
        super().__init__(name="Post-Process")

        self.input_mesh = None
        self.input_results = None

        static_tag = f"{self.tag}_static"
        dpg.delete_item(static_tag, children_only=True)

        with dpg.node_attribute(parent=self.node_tag,
                               attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_text("Visualization", bullet=True)
            dpg.add_combo(label="Field", items=["None", "Pressure", "Velocity Mag"],
                         default_value="None", tag=f"{self.tag}_field",
                         callback=self.update_view,
                         width=150)
            dpg.add_checkbox(label="Wireframe", tag=f"{self.tag}_wire")
            dpg.add_checkbox(label="Clip", tag=f"{self.tag}_clip")
            dpg.add_slider_float(label="Clip Plane Z", default_value=0.0,
                                min_value=-10, max_value=10,
                                tag=f"{self.tag}_clip_z", callback=self.update_view,
                                width=150)
            dpg.add_separator()
            dpg.add_button(label="Export VTK", callback=self.export_vtk)

    def set_input(self, attr_id, upstream_node):
        if hasattr(upstream_node, "results"):
            self.input_results = upstream_node.results
        if hasattr(upstream_node, "input_mesh"):
            self.input_mesh = upstream_node.input_mesh
        elif hasattr(upstream_node, "ms"):
            self.input_mesh = upstream_node.ms.current_mesh()
        self.update_view()

    def update_view(self, sender=None, data=None):
        if not self.input_mesh:
            return

        field_name = dpg.get_value(f"{self.tag}_field")
        wireframe = dpg.get_value(f"{self.tag}_wire")

        scalar = None
        if field_name == "Pressure" and self.input_results:
            scalar = self.input_results.get("pressure")
        elif field_name == "Velocity Mag" and self.input_results:
            # Fake velocity magnitude
            verts = self.input_mesh.vertex_matrix()
            scalar = np.linalg.norm(verts[:, :2], axis=1)

        clip_z = dpg.get_value(f"{self.tag}_clip_z") if dpg.get_value(f"{self.tag}_clip") else None

        get_app_singleton().viewer.load_mesh(
            self.input_mesh,
            scalar_field=scalar,
            colormap=dpg.mvPlotColormap_Viridis if scalar is not None else None,
            wireframe=wireframe,
            clip_plane=clip_z
        )

    def export_vtk(self, sender=None, data=None):
        if not self.input_mesh:
            return
        with dpg.file_dialog(directory_selector=True, show=True,
                            callback=self._save_vtk, modal=True):
            dpg.add_file_extension(".vtk")

    def _save_vtk(self, sender, app_data):
        import pyvista as pv
        path = list(app_data["selections"].values())[0]
        verts = self.input_mesh.vertex_matrix()
        faces = self.input_mesh.face_matrix()
        pv_mesh = pv.PolyData(verts, faces)
        if self.input_results and "pressure" in self.input_results:
            pv_mesh.point_data["Pressure"] = self.input_results["pressure"]
        pv_mesh.save(path)
        dpg.show_item("export_success")  # optional popup