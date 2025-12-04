# nodes/material.py
import dearpygui.dearpygui as dpg
from nodes.base_node import BaseNode
from app import get_app_singleton

class MaterialNode(BaseNode):
    def __init__(self):
        super().__init__(name="Material")
        self.props = {
            "name": "Steel",
            "density": 7800.0,
            "young_modulus": 210e9,
            "poisson": 0.3,
            "thermal_cond": 45.0,
            "specific_heat": 460.0
        }

        # Clean static area
        static_tag = f"{self.tag}_static"
        dpg.delete_item(static_tag, children_only=True)

        with dpg.node_attribute(parent=self.node_tag,
                               attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_text("Right-click → Properties", color=[180,180,180])

    def edit_properties(self):
        """This appears in the main property editor when node is selected"""
        dpg.add_text("Material Definition", bullet=True, color=[100, 200, 255])
        dpg.add_separator()

        def update(key):
            def cb(s, a):
                self.properties[key] = a
            return cb

        dpg.add_input_text(
            label="Name",
            default_value=self.properties["name"],
            callback=lambda s,a: self.properties.update(name=a)
        )

        dpg.add_input_float(
            label="Density [kg/m³]",
            default_value=self.properties["density"],
            format="%.2f",
            callback=update("density")
        )

        dpg.add_input_float(
            label="Young's Modulus [Pa]",
            default_value=self.properties["young_modulus"],
            format="%.3e",
            callback=update("young_modulus")
        )

        dpg.add_input_float(
            label="Poisson's Ratio",
            default_value=self.properties["poisson"],
            min_value=0.0, max_value=0.499,
            format="%.3f",
            callback=update("poisson")
        )

        dpg.add_separator()
        dpg.add_text("Thermal Properties", color=[255, 150, 100])
        dpg.add_input_float(
            label="Thermal Conductivity [W/m·K]",
            default_value=self.properties["thermal_conductivity"],
            callback=update("thermal_conductivity")
        )
        dpg.add_input_float(
            label="Specific Heat [J/kg·K]",
            default_value=self.properties["specific_heat"],
            callback=update("specific_heat")
        )