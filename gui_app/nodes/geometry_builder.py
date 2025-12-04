# nodes/geometry_builder.py
import dearpygui.dearpygui as dpg
import pymeshlab
import numpy as np
from nodes.base_node import BaseNode
from app import get_app_singleton

class GeometryBuilderNode(BaseNode):
    def __init__(self):
        super().__init__(name="Geometry Builder")

        self.ms = pymeshlab.MeshSet()
        self.current_id = 0
        self.shapes = {}  # id → dict of params

        # Clear placeholder
        static_tag = f"{self.tag}_static"
        dpg.delete_item(static_tag, children_only=True)

        with dpg.node_attribute(parent=self.node_tag,
                               attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_text("Add Primitive", bullet=True)
            with dpg.group(horizontal=True):
                dpg.add_combo(items=["Box", "Sphere", "Cylinder", "Cone", "Torus"],
                             default_value="Box", tag=f"{self.tag}_type", width=100)
                dpg.add_button(label="Add", callback=self.add_primitive)

            dpg.add_separator()
            dpg.add_text("Shapes", bullet=True)
            dpg.add_listbox(items=[], tag=f"{self.tag}_list", num_items=8,
                           callback=self.select_shape)

            with dpg.group(horizontal=True):
                dpg.add_button(label="Delete Selected", callback=self.delete_selected)
                dpg.add_button(label="Duplicate", callback=self.duplicate_selected)

            dpg.add_separator()
            dpg.add_text("Transform Selected", bullet=True)
            with dpg.group(horizontal=True):
                dpg.add_drag_float3(label="Translate", tag=f"{self.tag}_t", default_value=[0,0,0], speed=0.05)
                dpg.add_drag_float3(label="Rotate (deg)", tag=f"{self.tag}_r", default_value=[0,0,0], speed=1)
                dpg.add_drag_float3(label="Scale", tag=f"{self.tag}_s", default_value=[1,1,1], min_value=0.01, speed=0.02)

            dpg.add_separator()
            dpg.add_text("Boolean Operation", bullet=True)
            with dpg.group(horizontal=True):
                dpg.add_combo(items=["Union", "Difference", "Intersection"],
                             default_value="Union", tag=f"{self.tag}_bool")
                dpg.add_button(label="Apply to Selected Two", callback=self.apply_boolean)

            dpg.add_separator()
            dpg.add_button(label="Finalize & Triangulate", callback=self.finalize, width=-1)
            dpg.add_text("No geometry yet", tag=f"{self.tag}_status")

    def add_primitive(self):
        shape_type = dpg.get_value(f"{self.tag}_type")
        sid = self.current_id
        self.current_id += 1

        default = {
            "type": shape_type,
            "translate": [0,0,0],
            "rotate": [0,0,0],
            "scale": [1,1,1],
        }

        if shape_type == "Box":
            default.update({"size": [1,1,1]})
        elif shape_type == "Sphere":
            default.update({"radius": 0.5, "subdiv": 32})
        elif shape_type == "Cylinder":
            default.update({"radius": 0.5, "height": 1.0, "subdiv": 32})
        elif shape_type == "Cone":
            default.update({"r1": 0.5, "r2": 0.0, "height": 1.0, "subdiv": 32})
        elif shape_type == "Torus":
            default.update({"R": 1.0, "r": 0.3, "subdiv": 48})

        self.shapes[sid] = default
        self.update_listbox()
        self.select_shape(item=sid)

    def update_listbox(self):
        items = [f"{sid}: {data['type']}" for sid, data in self.shapes.items()]
        dpg.configure_item(f"{self.tag}_list", items=items)

    def select_shape(self, sender=None, item=None):
        if item is None:
            item = dpg.get_value(f"{self.tag}_list")
            if not item: return
            sid = int(item.split(":")[0])
        else:
            sid = item

        data = self.shapes.get(sid, {})
        dpg.set_value(f"{self.tag}_t", data.get("translate", [0,0,0]))
        dpg.set_value(f"{self.tag}_r", data.get("rotate", [0,0,0]))
        dpg.set_value(f"{self.tag}_s", data.get("scale", [1,1,1]))
        dpg.set_value(f"{self.tag}_list", f"{sid}: {data['type']}")

    def delete_selected(self):
        sel = dpg.get_value(f"{self.tag}_list")
        if not sel: return
        sid = int(sel.split(":")[0])
        self.shapes.pop(sid, None)
        self.update_listbox()

    def duplicate_selected(self):
        sel = dpg.get_value(f"{self.tag}_list")
        if not sel: return
        old_id = int(sel.split(":")[0])
        new_id = self.current_id
        self.current_id += 1
        self.shapes[new_id] = self.shapes[old_id].copy()
        self.update_listbox()

    def apply_boolean(self):
        items = dpg.get_value(f"{self.tag}_list")
        if len(self.shapes) < 2:
            return
        selected = [int(x.split(":")[0]) for x in dpg.get_value(f"{self.tag}_list") if ":" in x]
        if len(selected) < 2: return

        a_id, b_id = selected[-2], selected[-1]
        op = dpg.get_value(f"{self.tag}_bool")

        ms1 = self._create_mesh_from_shape(self.shapes[a_id])
        ms2 = self._create_mesh_from_shape(self.shapes[b_id])

        if op == "Union":
            ms1.boolean_union(ms2)
        elif op == "Difference":
            ms1.boolean_difference(ms2)
        elif op == "Intersection":
            ms1.boolean_intersection()

        # Replace first shape with result
        self.shapes[a_id] = {"type": f"{op} Result", "translate": [0,0,0], "rotate": [0,0,0], "scale": [1,1,1]}
        self.shapes.pop(b_id, None)
        self.update_listbox()
        dpg.set_value(f"{self.tag}_status", f"{op} applied")

    def _create_mesh_from_shape(self, shape):
        ms = pymeshlab.MeshSet()
        t = shape["translate"]
        r = np.radians(shape["rotate"])
        s = shape["scale"]

        if shape["type"] == "Box":
            ms.generate_box(xsiz=shape["size"][0]*2, ysiz=shape["size"][1]*2, zsiz=shape["size"][2]*2)
        elif shape["type"] == "Sphere":
            ms.generate_sphere(radius=shape["radius"], subdiv=shape["subdiv"])
        elif shape["type"] == "Cylinder":
            ms.generate_cylinder(radius=shape["radius"], height=shape["height"], subdiv=shape["subdiv"])
        elif shape["type"] == "Cone":
            ms.generate_cone(r1=shape["r1"], r2=shape["r2"], height=shape["height"], subdiv=shape["subdiv"])
        elif shape["type"] == "Torus":
            ms.generate_torus(major_r=shape["R"], minor_r=shape["r"], subdiv=shape["subdiv"])

        # Apply transforms
        ms.apply_coord_translation(t)
        if any(r): ms.apply_coord_rotation(axisx=r[0], axisy=r[1], axisz=r[2])
        if any(np.array(s) != 1): ms.apply_coord_scaling(scale=s)

        return ms

    def finalize(self):
        if not self.shapes:
            dpg.set_value(f"{self.tag}_status", "No shapes")
            return

        self.ms.clear()
        for shape in self.shapes.values():
            temp_ms = self._create_mesh_from_shape(shape)
            if not self.ms.is_empty():
                self.ms.boolean_union(temp_ms)
            else:
                self.ms = temp_ms

        # Final clean triangulated surface
        self.ms.remove_duplicate_vertices()
        self.ms.remove_duplicate_faces()
        self.ms.remove_unreferenced_vertices()

        result_mesh = self.ms.current_mesh()
        get_app_singleton().viewer.load_mesh(result_mesh, wireframe=False, color=[100, 200, 255, 255])

        dpg.set_item_label(self.node_tag, f"Builder: {result_mesh.vertex_number()} verts")
        dpg.set_value(f"{self.tag}_status", f"Finalized: {result_mesh.face_number()} triangles")

    def set_input(self, attr_id, upstream_node):
        pass  # this node has no input

    def execute(self, sender=None, data=None):
        self.finalize()