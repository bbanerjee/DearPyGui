# nodes/problem_setup.py
import dearpygui.dearpygui as dpg
from nodes.base_node import BaseNode
from nodes.material import MaterialNode
from nodes.boundary_condition import BoundaryConditionNode
from app import get_app_singleton

# These are the ONLY nodes allowed inside ProblemSetup
SUBNODE_REGISTRY = {
    "Material": "nodes/material.py::MaterialNode",
    "Boundary Condition": "nodes/boundary_condition.py::BoundaryConditionNode",
    "Load": "nodes/load.py::LoadNode",
    "Initial Condition": "nodes/initial_condition.py::InitialConditionNode",
}

class ProblemSetupNode(BaseNode):
    def __init__(self):
        super().__init__(name="Problem Setup")

        self.sub_editor_tag = f"sub_editor_{self.tag}"
        self.sub_nodes = {}

        # Replace static area with "Open Editor" button
        static_tag = f"{self.tag}_static"
        dpg.delete_item(static_tag, children_only=True)

        with dpg.node_attribute(parent=self.node_tag,
                               attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_button(label="Open Problem Setup Editor",
                          callback=self.open_sub_editor, width=-1)
            dpg.add_text("Double-click node or click button", color=[150,150,150])

    def open_sub_editor(self):
        app = get_app()

        # Create modal window with its own node editor
        if not dpg.does_item_exist(self.sub_editor_tag):
            with dpg.window(label=f"Problem Setup — {self.name}",
                           modal=True, width=1000, height=700,
                           tag=self.sub_editor_tag, pos=[200, 50]):

                with dpg.menu_bar():
                    dpg.add_text("Problem Definition Nodes")
                    dpg.add_spacer(width=20)
                    dpg.add_button(label="Close", callback=lambda: dpg.delete_item(self.sub_editor_tag))

                with dpg.group(horizontal=True):
                    # Left: sub-node library
                    with dpg.child_window(width=250):
                        dpg.add_text("Add Definition", bullet=True)
                        dpg.add_separator()
                        for name in ["Material", "Boundary Condition", "Load", "Initial Condition"]:
                            dpg.add_button(label=name, width=-1, height=40,
                                          callback=lambda s,a,u=name: self.create_subnode(u))

                    # Center: sub-node canvas
                    with dpg.child_window():
                        with dpg.node_editor(tag=f"sub_canvas_{self.tag}",
                                            minimap=True,
                                            callback=self.sub_link,
                                            delink_callback=self.sub_delink) as canvas:
                            pass

        dpg.show_item(self.sub_editor_tag)
        dpg.focus_item(self.sub_editor_tag)

    def create_subnode(self, node_type_name):
        # Dynamically import and instantiate
        module_path, class_name = SUBNODE_REGISTRY[node_type_name].split("::")
        module = __import__(module_path.replace(".py", "").replace("/", "."), fromlist=[class_name])
        cls = getattr(module, class_name)
        instance = cls()
        instance.parent_setup = self  # reference back
        self.sub_nodes[instance.node_tag] = instance

    def sub_link(self, sender, app_data):
        # Sub-node linking logic (you can expand later)
        pass

    def sub_delink(self, sender, app_data):
        pass

    def get_materials(self):
        return [n for n in self.sub_nodes.values() if isinstance(n, MaterialNode)]

    def get_boundary_conditions(self):
        return [n for n in self.sub_nodes.values() if isinstance(n, BoundaryConditionNode)]