from nodes.base_node import BaseNode
import dearpygui.dearpygui as dpg
from app import get_app_singleton
import pymeshlab
import os

class ImportGeometryNode(BaseNode): 
    def __init__(self):
        print("Init ImportGeometryNode")
        super().__init__(name="Import Geometry")
        self.file_path = ""
        self.mesh_set = None

        self.create_node_ui_local()

    def create_node_ui_local(self):
        print(f"Creating UI for node: {self.name} tag: {self.node_tag} parent: {self.app.node_editor_tag}")

        # Create unique tag for this node's file dialog
        file_dialog_tag = f"{self.node_tag}_file_dialog"

        # ── Replace the placeholder static attribute with real controls ──
        static_tag = f"{self.node_tag}_static"
        dpg.delete_item(static_tag, children_only=True)  # clear placeholder

        print(f"Adding file browser to node: {self.name}, parent: {self.node_tag}, file_dialog_tag: {file_dialog_tag}")
        #with dpg.node_attribute(parent=self.node_tag, 
        #                        attribute_type=dpg.mvNode_Attr_Static):
        dpg.add_button(label="Browse ...", 
                       callback=lambda: dpg.show_item(file_dialog_tag),
                       parent=static_tag)

        print(f"Creating file dialog with tag: {file_dialog_tag}")
        with dpg.file_dialog(
                directory_selector=False,
                show=False,
                callback=self.load_file, 
                tag=file_dialog_tag,
                width=700, height=400):
            dpg.add_file_extension("*.obj", color=(150, 255, 150, 255))
            dpg.add_file_extension(".stl", color=(150, 255, 150, 255))
            dpg.add_file_extension(".ply", color=(150, 255, 150, 255))
            dpg.add_file_extension(".off", color=(150, 255, 150, 255))
            dpg.add_file_extension(".3ds", color=(150, 255, 150, 255))
            dpg.add_file_extension(".dae", color=(150, 255, 150, 255))
            dpg.add_file_extension(".fbx", color=(150, 255, 150, 255))
            dpg.add_file_extension(".gltf", color=(150, 255, 150, 255))
            dpg.add_file_extension(".glb", color=(150, 255, 150, 255))

    def load_file(self, sender, app_data):
        self.file_path = list(app_data["selections"].values())[0]
        ms = pymeshlab.MeshSet()
        ms.load_new_mesh(self.file_path)
        print(f"Loaded {self.file_path}")
        self.mesh_set = ms

        get_app_singleton().viewer.load_mesh(ms.current_mesh())
        self.execute()

    def execute(self, sender=None, app_data=None):
        if self.mesh_set:
            dpg.set_item_label(self.node_tag, f"Geometry: {os.path.basename(self.file_path)}")

    def clear_input(self):
        self.input_mesh = None
        self.mesh_set = None
        self.output_mesh = None
        dpg.set_item_label(self.node_tag, self.name)
        dpg.set_value(f"{self.tag}_status", "Status: waiting for input...") if hasattr(self, f"{self.tag}_status") else None

