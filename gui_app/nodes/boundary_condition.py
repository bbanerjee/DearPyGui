# nodes/boundary_condition.py
import dearpygui.dearpygui as dpg
from nodes.base_node import BaseNode
from app import get_app_singleton

class BoundaryConditionNode(BaseNode):
    def __init__(self):
        super().__init__(name="Boundary Condition")
        self.bc_type = "Fixed"
        self.value = [0.0, 0.0, 0.0]
        # ... UI ...

    def edit_properties(self):

        def callback_wrapper(key):
            def cb(s, a):
                setattr(self, key, a)
                self.execute()  # or trigger downstream
            return cb

        # Using callback_wrapper to avoid late binding issue
        #dpg.add_input_float(..., callback=callback_wrapper("density"))

        dpg.add_combo(label="Type", items=["Fixed", "Pressure", "Velocity", "Temperature"],
                     default_value=self.bc_type,
                     callback=lambda s,a: setattr(self, "bc_type", a))

        if self.bc_type == "Fixed":
            dpg.add_checkbox(label="Fix X", default_value=True)
            dpg.add_checkbox(label="Fix Y", default_value=True)
            dpg.add_checkbox(label="Fix Z", default_value=True)

        elif self.bc_type == "Pressure":
            dpg.add_input_float(label="Pressure [Pa]", default_value=1e5, format="%.1f")

        elif self.bc_type == "Velocity":
            dpg.add_drag_float3(label="Velocity [m/s]", default_value=self.value)

        elif self.bc_type == "Temperature":
            dpg.add_input_float(label="Temperature [K]", default_value=293.15)