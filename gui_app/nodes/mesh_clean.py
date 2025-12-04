# nodes/mesh_clean.py
import dearpygui.dearpygui as dpg
import pymeshlab
from nodes.base_node import BaseNode
from app import get_app_singleton

class MeshCleanNode(BaseNode):
    def __init__(self):
        super().__init__("Mesh Clean & Repair")
        self.input_mesh = None
        self.mesh_set = None

        # ── Replace the placeholder static attribute with real controls ──
        static_tag = f"{self.node_tag}_static"
        dpg.delete_item(static_tag, children_only=True)  # clear placeholder

        with dpg.node_attribute(parent=self.node_tag,
                               attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_text("Repair Options", bullet=True)
            dpg.add_checkbox(label="Remove duplicate vertices",
                            default_value=True, tag=f"{self.tag}_dup_v")
            dpg.add_checkbox(label="Remove duplicate faces",
                            default_value=True, tag=f"{self.tag}_dup_f")
            dpg.add_checkbox(label="Remove zero-area faces",
                            default_value=True, tag=f"{self.tag}_zero")
            dpg.add_checkbox(label="Fix orientation",
                            default_value=True, tag=f"{self.tag}_orient")
            dpg.add_separator()
            dpg.add_button(label="Clean Now", callback=self.execute)

    def set_input(self, attr_id, upstream_node):
        # Called automatically when someone connects to our input pin
        print(f"{self.name} received input from {upstream_node.name}")
        if hasattr(upstream_node, "mesh_set") and upstream_node.mesh_set:
            self.input_mesh = upstream_node.mesh_set.current_mesh()
            self.mesh_set = upstream_node.mesh_set
            self.execute()  # auto-run when input arrives
        elif hasattr(upstream_node, "output_mesh"):
            self.input_mesh = upstream_node.output_mesh
            self.mesh_set = pymeshlab.MeshSet()
            self.mesh_set.add_mesh(self.input_mesh)
            self.execute()

    def execute(self, sender=None, data=None):
        if self.input_mesh is None and (self.mesh_set is None or self.mesh_set.is_empty()):
            dpg.set_item_label(self.node_tag, "Mesh Clean (no input)")
            return

        if self.mesh_set is None:
            self.mesh_set = pymeshlab.MeshSet()
            self.mesh_set.add_mesh(self.input_mesh)

        # Apply selected repairs
        if dpg.get_value(f"{self.tag}_dup_v"):
            self.mesh_set.remove_duplicate_vertices()
        if dpg.get_value(f"{self.tag}_dup_f"):
            self.mesh_set.remove_duplicate_faces()
        if dpg.get_value(f"{self.tag}_zero"):
            self.mesh_set.remove_zero_area_faces()
        if dpg.get_value(f"{self.tag}_orient"):
            self.mesh_set.coherent_orientation()

        # Show result in 3D viewer
        cleaned = self.mesh_set.current_mesh()
        get_app_singleton().viewer.load_mesh(cleaned)

        dpg.set_item_label(self.node_tag,
                          f"Cleaned: {cleaned.vertex_number()} verts, {cleaned.face_number()} faces")

    def clear_input(self):
        self.input_mesh = None
        self.mesh_set = None
        self.output_mesh = None
        dpg.set_item_label(self.node_tag, self.name)
        dpg.set_value(f"{self.tag}_status", "Status: waiting for input...") if hasattr(self, f"{self.tag}_status") else None
