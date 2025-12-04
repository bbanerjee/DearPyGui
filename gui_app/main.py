import dearpygui.dearpygui as dpg
import pymeshlab
import os
import platform

from app import get_app_singleton
from nodes.base_node import BaseNode
from nodes.import_geometry import ImportGeometryNode
from nodes.geometry_builder import GeometryBuilderNode
from nodes.mesh_clean import MeshCleanNode
from nodes.generate_mesh import GenerateMeshNode
from nodes.problem_setup import ProblemSetupNode
from nodes.solver import SolverNode
from nodes.postprocess import PostProcessNode

# Global registry for nodes
NODE_REGISTRY = {
    "ImportGeometryNode": ImportGeometryNode,
    "GeometryBuilderNode": GeometryBuilderNode,
    "MeshCleanNode": MeshCleanNode,
    "GenerateMeshNode": GenerateMeshNode,
    "ProblemSetupNode": ProblemSetupNode,
    "SolverNode": SolverNode,
    "PostProcessNode": PostProcessNode,
}

PROPERTY_EDITOR_TAG = "property_editor"

def clear_property_editor():
    dpg.delete_item(PROPERTY_EDITOR_TAG, children_only=True)
    dpg.add_text("Select a node to edit properties", parent=PROPERTY_EDITOR_TAG)

def show_node_properties(node_instance):
    clear_property_editor()
    if not node_instance or not hasattr(node_instance, "edit_properties"):
        dpg.add_text("This node has no editable properties", parent=PROPERTY_EDITOR_TAG)
        return

    with dpg.group(parent=PROPERTY_EDITOR_TAG):
        node_instance.edit_properties()

def on_node_click(sender, app_data):
    """Handles left-click on nodes — updates property editor"""
    # app_data[1] is the item clicked (node tag)
    clicked_item = app_data[1]
    item_type = dpg.get_item_type(clicked_item)

    if item_type == dpg.mvItemType_Node:  # It's a node!
        app = get_app_singleton()
        node = app.nodes.get(clicked_item)

        # Search sub-nodes if not found in main graph
        if not node:
            for main_node in list(app.nodes.values()):
                if hasattr(main_node, "sub_nodes") and main_node.sub_nodes:
                    node = main_node.sub_nodes.get(clicked_item)
                    if node:
                        break

        if node:
            show_node_properties(node)
        else:
            clear_property_editor()

def create_node_callback(sender, app_data, user_data):
    node_class = NODE_REGISTRY[user_data]
    node_class()                               # instantiates and auto-registers via BaseNode

# Global storage for links: link_id → (output_node_instance, input_node_instance)
LINKS = {}

def link_callback(sender, app_data):
    """Called when user creates a link: app_data = [output_attr_tag, input_attr_tag]"""
    print("link_callback: app_data", app_data)
    output_attr_tag = app_data[0]
    input_attr_tag = app_data[1]

    # Find the nodes that own these attributes
    output_node_id = dpg.get_item_parent(output_attr_tag)
    input_node_id = dpg.get_item_parent(input_attr_tag)
    print(f"Linking from {output_node_id} to {input_node_id}")

    output_node_tag = dpg.get_item_alias(output_node_id)
    input_node_tag = dpg.get_item_alias(input_node_id)

    output_node = None
    input_node = None

    app = get_app_singleton()
    for node in app.nodes.values():
        print(f"Checking node: {node} input: {input_node_tag} output: {output_node_tag} tag: {node.node_tag}")
        if node.node_tag == output_node_tag:
            output_node = node
        if node.node_tag == input_node_tag:
            input_node = node

    if not output_node or not input_node:
        print("Warning: Link involves unknown node")
        return

    # Store the link for delink handling
    link_id = dpg.add_node_link(output_attr_tag, input_attr_tag, parent=sender)
    LINKS[link_id] = (output_node, input_node)

    # Notify the downstream node that it now has a new input
    input_node.set_input(input_attr_tag, output_node)

    print(f"Linked: {output_node.name} → {input_node.name}")

def delink_callback(sender, app_data):
    """Called when user deletes a link: app_data = link_id"""
    link_id = app_data

    if link_id not in LINKS:
        return

    output_node, input_node = LINKS[link_id]

    # Optional: tell the downstream node to clear its input/cache
    if hasattr(input_node, "clear_input"):
        input_node.clear_input()
    else:
        # Default fallback: just resets internal state
        input_node.input_mesh = None
        input_node.ms = None
        input_node.output_mesh = None
        dpg.set_item_label(input_node.node_tag, input_node.name)

    print(f"Unlinked: {output_node.name} → {input_node.name}")

    # Remove from tracking
    del LINKS[link_id]
    dpg.delete_item(link_id)


def node_selected(sender, app_data):
    selected_nodes = dpg.get_selected_nodes(sender)
    if not selected_nodes:
        clear_property_editor()
        return
    
    node_tag = selected_nodes[0]  # take first selected

    # Search in main nodes and all open sub-editors
    node = get_app_singleton().nodes.get(node_tag)
    if not node:
        # Search inside any ProblemSetup sub-nodes
        for main_node in get_app_singleton().nodes.values():
            if hasattr(main_node, "sub_nodes"):
                node = main_node.sub_nodes.get(node_tag)
                if node:
                    break

    if node and hasattr(node, "edit_properties"):
        show_node_properties(node)
    else:
        clear_property_editor()

def load_vscode_font():
    with dpg.font_registry():
        system = platform.system()
        
        if system == "Windows":
            font_path = "C:/Windows/Fonts/consola.ttf"
        elif system == "Darwin":  # macOS
            font_path = "/System/Library/Fonts/Menlo.ttc"
        else:  # Linux
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
        
        try:
            default_font = dpg.add_font(font_path, 15)
            dpg.bind_font(default_font)
            print(f"Loaded font: {font_path}")
        except Exception as e:
            print(f"Could not load font {font_path}: {e}")
            print("Using default DearPyGui font")


def create_dark_theme():
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvAll):
            # Background colors
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (20, 20, 30, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (25, 25, 35, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (35, 35, 45, 255))
            
            # Text
            dpg.add_theme_color(dpg.mvThemeCol_Text, (220, 220, 230, 255))
            
            # Buttons
            dpg.add_theme_color(dpg.mvThemeCol_Button, (50, 50, 70, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (70, 70, 90, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (80, 80, 100, 255))
            
            # Rounding
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
            
    return theme

def create_light_theme():
    with dpg.theme() as light_theme:
        with dpg.theme_component(dpg.mvAll):
            # Background colors
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (240, 240, 245, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (250, 250, 252, 255))
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (255, 255, 255, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Border, (200, 200, 210, 255))
            
            # Frame/Input backgrounds
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (255, 255, 255, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (245, 245, 250, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (235, 235, 245, 255))
            
            # Text
            dpg.add_theme_color(dpg.mvThemeCol_Text, (20, 20, 25, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, (140, 140, 150, 255))
            
            # Title bar
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (230, 230, 240, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (220, 220, 235, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgCollapsed, (240, 240, 245, 255))
            
            # Buttons
            dpg.add_theme_color(dpg.mvThemeCol_Button, (200, 200, 215, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (180, 180, 200, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (160, 160, 185, 255))
            
            # Headers
            dpg.add_theme_color(dpg.mvThemeCol_Header, (220, 220, 235, 255))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (210, 210, 230, 255))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (200, 200, 225, 255))
            
            # Tabs
            dpg.add_theme_color(dpg.mvThemeCol_Tab, (230, 230, 240, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TabHovered, (210, 210, 230, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TabActive, (245, 245, 250, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TabUnfocused, (235, 235, 242, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TabUnfocusedActive, (240, 240, 245, 255))
            
            # Scrollbar
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, (245, 245, 248, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, (200, 200, 210, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, (180, 180, 195, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive, (160, 160, 180, 255))
            
            # Checkmarks and sliders
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, (60, 120, 200, 255))
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (70, 130, 210, 255))
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (50, 110, 190, 255))
            
            # Separators
            dpg.add_theme_color(dpg.mvThemeCol_Separator, (200, 200, 210, 255))
            dpg.add_theme_color(dpg.mvThemeCol_SeparatorHovered, (180, 180, 200, 255))
            dpg.add_theme_color(dpg.mvThemeCol_SeparatorActive, (160, 160, 190, 255))
            
            # Resize grip
            dpg.add_theme_color(dpg.mvThemeCol_ResizeGrip, (200, 200, 210, 100))
            dpg.add_theme_color(dpg.mvThemeCol_ResizeGripHovered, (180, 180, 200, 170))
            dpg.add_theme_color(dpg.mvThemeCol_ResizeGripActive, (160, 160, 190, 240))
            
            # Menu bar
            dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, (235, 235, 242, 255))
            
            # ========== NODE EDITOR COLORS ==========
            # Node background
            dpg.add_theme_color(dpg.mvNodeCol_NodeBackground, (255, 255, 255, 255))
            dpg.add_theme_color(dpg.mvNodeCol_NodeBackgroundHovered, (248, 248, 252, 255))
            dpg.add_theme_color(dpg.mvNodeCol_NodeBackgroundSelected, (240, 245, 255, 255))
            
            # Node outline/border
            dpg.add_theme_color(dpg.mvNodeCol_NodeOutline, (180, 180, 195, 255))
            
            # Title bar
            dpg.add_theme_color(dpg.mvNodeCol_TitleBar, (220, 220, 235, 255))
            dpg.add_theme_color(dpg.mvNodeCol_TitleBarHovered, (210, 210, 230, 255))
            dpg.add_theme_color(dpg.mvNodeCol_TitleBarSelected, (200, 210, 235, 255))
            
            # Links (connections between nodes)
            dpg.add_theme_color(dpg.mvNodeCol_Link, (70, 130, 210, 255))
            dpg.add_theme_color(dpg.mvNodeCol_LinkHovered, (90, 150, 230, 255))
            dpg.add_theme_color(dpg.mvNodeCol_LinkSelected, (50, 110, 190, 255))
            
            # Pins (connection points)
            dpg.add_theme_color(dpg.mvNodeCol_Pin, (70, 130, 210, 255))
            dpg.add_theme_color(dpg.mvNodeCol_PinHovered, (90, 150, 230, 255))
            
            # Box selector (when dragging to select multiple nodes)
            dpg.add_theme_color(dpg.mvNodeCol_BoxSelector, (70, 130, 210, 80))
            dpg.add_theme_color(dpg.mvNodeCol_BoxSelectorOutline, (70, 130, 210, 255))
            
            # Grid lines in node editor background
            dpg.add_theme_color(dpg.mvNodeCol_GridBackground, (250, 250, 252, 255))
            dpg.add_theme_color(dpg.mvNodeCol_GridLine, (230, 230, 235, 255))
            
            # Style variables
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 3)
            dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 9)
            
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 10, 10)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 6, 4)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ItemInnerSpacing, 6, 6)
            
            # Node-specific style variables
            dpg.add_theme_style(dpg.mvNodeStyleVar_NodeCornerRounding, 6)
            dpg.add_theme_style(dpg.mvNodeStyleVar_NodePadding, 8, 8)
            dpg.add_theme_style(dpg.mvNodeStyleVar_NodeBorderThickness, 1.5)
            dpg.add_theme_style(dpg.mvNodeStyleVar_LinkThickness, 3)
            dpg.add_theme_style(dpg.mvNodeStyleVar_PinCircleRadius, 5)
            dpg.add_theme_style(dpg.mvNodeStyleVar_PinQuadSideLength, 8)
            
    return light_theme

# Apply it
dpg.create_context()
#dpg.bind_theme(create_dark_theme())
dpg.bind_theme(create_light_theme())
load_vscode_font()

dpg.create_viewport(title='Engineering Pipeline Studio', width=1600, height=1000)
app = get_app_singleton()
#dpg.set_item_user_data("app", app)          # cheap way to make it reachable from callback

# Add handler IMMEDIATELY after context/viewport, wrapped in registry
with dpg.handler_registry(tag="global_node_selector"):  # Clean registry tag
    dpg.add_mouse_click_handler(
        button=dpg.mvMouseButton_Left,  # Left-click to select
        callback=on_node_click
    )

with dpg.window(tag="MainWindow", label="main_window"):
    with dpg.menu_bar():
        with dpg.menu(label="File"):
            dpg.add_menu_item(label="New")
            dpg.add_menu_item(label="Load")
            dpg.add_menu_item(label="Save")
        with dpg.menu(label="View"):
            dpg.add_menu_item(label="3D Viewer", callback=lambda: app.viewer.show())
        with dpg.menu(label="Layout"):
            dpg.add_menu_item(label="Reset Auto-Layout", 
                              callback=lambda: get_app_singleton().reset_layout())

    with dpg.group(horizontal=True):

        # Left: Node palette 
        with dpg.child_window(width=250, autosize_y=True):
            with dpg.child_window(height=400, autosize_x=True, border=False):
                dpg.add_text("Node Library", bullet=True)
                dpg.add_separator()
                for node_name in NODE_REGISTRY.keys():
                    dpg.add_button(label=node_name.replace("Node", ""),
                                width=-1, height=35,
                                callback=create_node_callback,
                                user_data=node_name)

            # Left bottom: Property editor 
            with dpg.child_window(autosize_x=True, border=True):
                dpg.add_text("Properties", bullet=True)
                dpg.add_separator()
                with dpg.group(tag=PROPERTY_EDITOR_TAG):
                    dpg.add_text("Select a node to edit properties")

        # Center: Node editor
        with dpg.child_window(autosize_x=True, autosize_y=True):
            with dpg.node_editor(callback=link_callback,
                                 delink_callback=delink_callback,
                                 #selection_callback=node_selected,
                                 minimap=True,
                                 minimap_location=dpg.mvNodeMiniMap_Location_BottomRight,
                                 tag="node_editor") as node_editor_tag:
                print("Created node editor with tag", node_editor_tag)
                app.node_editor_tag = node_editor_tag


# Store nodes in app singleton so link_callback can find them
app.nodes = {}  # will be filled when nodes call BaseNode.__init__

# Initial clear
clear_property_editor()

dpg.setup_dearpygui()
dpg.set_primary_window("MainWindow", True)
dpg.show_viewport()

while dpg.is_dearpygui_running():
    dpg.render_dearpygui_frame()

dpg.destroy_context()
