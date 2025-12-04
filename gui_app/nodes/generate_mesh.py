# nodes/generate_mesh.py
import dearpygui.dearpygui as dpg
import pymeshlab
from nodes.base_node import BaseNode
from app import get_app_singleton

class GenerateMeshNode(BaseNode):
    def __init__(self):
        super().__init__("Tetrahedral Mesh")
        self.input_mesh = None
        self.output_mesh = None
        self.mesh_set = None

        with dpg.node_attribute(parent=self.node_tag,
                               attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_text("TetGen Parameters", bullet=True)
            dpg.add_slider_float(label="Max cell volume",
                                default_value=1.0, 
                                min_value=0.001, max_value=100.0,
                                tag=f"{self.tag}_vol",
                                width=200)
            dpg.add_slider_float(label="Max radius-edge ratio",
                                default_value=2.0,
                                min_value=1.0, max_value=5.0,
                                tag=f"{self.tag}_ratio",
                                width=200)
            dpg.add_checkbox(label="Preserve boundary",
                            default_value=True, tag=f"{self.tag}_preserve")
            #dpg.add_separator()
            dpg.add_text("_" * 20)
            dpg.add_button(label="Generate Volume Mesh", callback=self.execute)
            dpg.add_text("Status: waiting for surface mesh...", tag=f"{self.tag}_status")

    def set_input(self, attr_id, upstream_node):
        # Accept cleaned surface mesh from previous node
        if upstream_node and hasattr(upstream_node, "mesh_set") and upstream_node.mesh_set:
            # Upstream node has a MeshSet, use it directly
            self.mesh_set = upstream_node.mesh_set
            
        elif upstream_node and hasattr(upstream_node, "input_mesh") and upstream_node.input_mesh is not None:
            # Upstream node has input_mesh, create new MeshSet and add it
            try:
                self.mesh_set = pymeshlab.MeshSet()
                # input_mesh should be a pymeshlab.Mesh object
                self.mesh_set.add_mesh(upstream_node.input_mesh)
            except Exception as e:
                print(f"Error adding mesh from input_mesh: {e}")
                self.mesh_set = pymeshlab.MeshSet()  # Create empty MeshSet
                
        else:
            # No valid mesh found
            print(f"Warning: No valid mesh found in upstream node {upstream_node.name if upstream_node else 'None'}")
            self.mesh_set = pymeshlab.MeshSet()  # Create empty MeshSet
        
        self.execute()

    def execute(self, sender=None, data=None):
        if not self.mesh_set or self.mesh_set.is_empty():
            dpg.set_value(f"{self.tag}_status", "Error: No surface mesh")
            return

        # Ensure we have a watertight surface
        self.mesh_set.compute_normal_for_point_clouds()  # just in case
        self.mesh_set.remove_unreferenced_vertices()

        # Generate tetrahedral mesh using built-in PyMeshLab TetGen wrapper
        max_vol = dpg.get_value(f"{self.tag}_vol")
        ratio = dpg.get_value(f"{self.tag}_ratio")
        preserve = dpg.get_value(f"{self.tag}_preserve")

        flags = "pq"
        flags += f"Y" if preserve else ""   # Y = preserve boundary facets
        flags += f"a{ max_vol }"            # a = max volume
        flags += f"q{ratio}"                # q = radius-edge ratio

        try:
            self.mesh_set.generate_tetrahedralization_with_tetgen(flags=flags)
            tet_mesh = self.mesh_set.current_mesh()

            # Visualize the volume mesh (wireframe + semi-transparent)
            get_app_singleton().viewer.load_mesh(tet_mesh, wireframe=True, opacity=0.6)

            dpg.set_value(f"{self.tag}_status",
                         f"Success: {tet_mesh.vertex_number()} verts, {tet_mesh.cell_number()} tets")
            dpg.set_item_label(self.node_tag,
                              f"Tet Mesh: {tet_mesh.cell_number()} elements")

            self.output_mesh = tet_mesh

        except Exception as e:
            dpg.set_value(f"{self.tag}_status", f"Error: {str(e)}")

    def clear_input(self):
        self.input_mesh = None
        self.mesh_set = None
        self.output_mesh = None
        dpg.set_item_label(self.node_tag, self.name)
        dpg.set_value(f"{self.tag}_status", "Status: waiting for input...") if hasattr(self, f"{self.tag}_status") else None
