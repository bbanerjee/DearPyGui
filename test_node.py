import dearpygui.dearpygui as dpg
import random


# Node data structure
class Node:
    def __init__(self, label, pos=[50, 50]):
        self.id = random.randint(1, 2**32 - 1)
        self.label = label
        self.pos = list(pos)
        self.inputs = {}  # {connector_id: {'name': str, 'type': str, 'value': any}}
        self.outputs = {}  # {connector_id: {'name': str, 'type': str, 'value': any}}
        self.params = {}  # Step-specific parameters


nodes = {}
links = {}
node_counter = 0


def add_curr_node(sender, app_data):
    global node_counter
    curr_node_id = f"node_{node_counter}"
    curr_node = Node(
        label=app_data, pos=[50 + node_counter * 50, 50 + node_counter * 50]
    )
    nodes[curr_node_id] = curr_node
    node_counter += 1
    draw_node(curr_node_id, curr_node)


def draw_node(curr_node_id, curr_node):
    with dpg.node(
        tag=curr_node_id, pos=curr_node.pos, label=curr_node.label, parent="node_editor"
    ):
        # Input connectors
        for conn_id, connector in curr_node.inputs.items():
            print("Add input conn", conn_id)
            #dpg.add_node_attribute(tag=conn_id, attribute_type=dpg.mvNode_Attr_Input)
            with dpg.node_attribute(tag=conn_id, attribute_type=dpg.mvNode_Attr_Input):
                dpg.add_text(label=connector["name"])

        # Parameters (simplified for now)
        # with dpg.group():
        for param_name, param_value in curr_node.params.items():
            if isinstance(param_value, float):
                print("test")
                with dpg.node_attribute(
                    label=param_name, attribute_type=dpg.mvNode_Attr_Input
                ):
                    dpg.add_input_float(
                        label=param_name,
                        default_value=param_value,
                        callback=lambda s, a: nodes[curr_node_id].params.update(
                            {param_name: a}
                        ),
                    )
            elif isinstance(param_value, bool):
                print("test")
                with dpg.node_attribute(
                    label=param_name, attribute_type=dpg.mvNode_Attr_Input
                ):
                    dpg.add_checkbox(
                        label=param_name,
                        default_value=param_value,
                        callback=lambda s, a: nodes[curr_node_id].params.update(
                            {param_name: a}
                        ),
                    )
            elif (
                isinstance(param_value, int) and "items" in connector
            ):  # Assuming combo if int and has 'items'
                print("test")
                with dpg.node_attribute(
                    label=param_name, attribute_type=dpg.mvNode_Attr_Input
                ):
                    dpg.add_combo(
                        label=param_name,
                        items=connector["items"],
                        default_value=connector["items"][param_value],
                        callback=lambda s, a: nodes[curr_node_id].params.update(
                            {param_name: connector["items"].index(a)}
                        ),
                    )
            else:
                print("test")
                with dpg.node_attribute(
                    label=param_name, attribute_type=dpg.mvNode_Attr_Input
                ):
                    dpg.add_text(f"{param_name}: {param_value}")

        # Output connectors
        for conn_id, connector in curr_node.outputs.items():
            print("Add output conn", conn_id)
            #dpg.add_node_attribute(tag=conn_id, attribute_type=dpg.mvNode_Attr_Output)
            with dpg.node_attribute(tag=conn_id, attribute_type=dpg.mvNode_Attr_Output):
                dpg.add_text(label=connector["name"])


def link_callback(sender, app_data):
    output_attr = app_data[0]
    input_attr = app_data[1]
    print("link_callback: app_data", app_data)
    link_id = random.randint(1, 2**32 - 1)
    links[link_id] = (output_attr, input_attr)
    dpg.add_node_link(output_attr, input_attr, parent="node_editor", tag=link_id)


def delink_callback(sender, app_data):
    link_id = app_data
    print("delink_callback: app_data", app_data)
    if link_id in links:
        del links[link_id]
        dpg.delete_item(link_id)


def run_analysis(sender, app_data):
    # Basic execution order (very simplified)
    ordered_nodes = []
    visited = set()

    def get_downstream_nodes(node_id):
        downstream = set()
        for link_id, (output, input) in links.items():
            if output.split("##")[0] in nodes[node_id].outputs:
                input_node_id = input.split("##")[0]
                downstream.add(input_node_id)
                downstream.update(get_downstream_nodes(input_node_id))
        return downstream

    # Simple topological sort (handle cycles more robustly in a real app)
    in_degree = {node_id: 0 for node_id in nodes}
    adj = {node_id: [] for node_id in nodes}

    for link_id, (output, input) in links.items():
        output_node_id = output.split("##")[0]
        input_node_id = input.split("##")[0]
        print(f"output : {output_node_id}, input: {input_node_id}")
        adj.setdefault(output_node_id, []).append(input_node_id)
        if input_node_id not in in_degree:
            in_degree[input_node_id] = 0
        in_degree[input_node_id] += 1

    queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
    while queue:
        current_node_id = queue.pop(0)
        ordered_nodes.append(current_node_id)
        for neighbor in adj[current_node_id]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    print("Execution Order:", ordered_nodes)
    # In a real application, you would process the nodes in order,
    # passing data between them based on the links.
    for node_id in ordered_nodes:
        print(
            f"Processing node: {nodes[node_id].label} with params: {nodes[node_id].params}"
        )


dpg.create_context()

with dpg.window(label="Node Editor Example", width=800, height=600):
    with dpg.node_editor(tag="node_editor", 
                         callback=link_callback,
                         delink_callback=delink_callback):
        pass

with dpg.window(label="Add Node", width=200):
    print("Creating Add node window")
    dpg.add_input_text(tag="new_node_label", hint="Node Label")
    dpg.add_button(
       label="Add Data Input", callback=add_curr_node, user_data="Data Input"
    )
    dpg.add_button(
       label="Add Preprocessing", callback=add_curr_node, user_data="Preprocessing"
    )
    dpg.add_button(label="Add Analysis", callback=add_curr_node, user_data="Analysis")
    dpg.add_button(
       label="Add Post-processing", callback=add_curr_node, user_data="Post-processing"
    )
    dpg.add_button(label="Add Results", callback=add_curr_node, user_data="Results")
    dpg.add_button(label="Run Analysis", callback=run_analysis)

# Define initial nodes with connectors (example)
initial_nodes_data = {
    "data_input_node": Node(label="Data Input", pos=[100, 100]),
    "preprocess_node": Node(label="Preprocessing", pos=[300, 100]),
    "analysis_node": Node(label="Analysis", pos=[300, 250]),
    "results_node": Node(label="Results", pos=[500, 100]),
}

initial_nodes_data["data_input_node"].outputs["output_data"] = {
    "name": "Data",
    "type": "float",
}
initial_nodes_data["data_input_node"].params["input_value_1"] = 2.0
initial_nodes_data["data_input_node"].params["input_value_2"] = 5.0

initial_nodes_data["preprocess_node"].inputs["input_data"] = {
    "name": "Data In",
    "type": "float",
}
initial_nodes_data["preprocess_node"].outputs["output_processed"] = {
    "name": "Processed",
    "type": "float",
}
initial_nodes_data["preprocess_node"].params["scale"] = 1.5

initial_nodes_data["analysis_node"].inputs["input_processed"] = {
    "name": "Processed In",
    "type": "float",
}
initial_nodes_data["analysis_node"].outputs["output_analyzed"] = {
    "name": "Analyzed",
    "type": "float",
}
initial_nodes_data["analysis_node"].params["iterations"] = 10

initial_nodes_data["results_node"].inputs["input_result"] = {
    "name": "Result In",
    "type": "float",
}

for node_id, node in initial_nodes_data.items():
    nodes[node_id] = node
    print("Adding node")
    draw_node(node_id, node)

# Define initial links (example)
#links_data = [
#    ("data_input_node##output_data", "preprocess_node##input_data"),
#    ("preprocess_node##output_processed", "analysis_node##input_processed"),
#    ("analysis_node##output_analyzed", "results_node##input_result"),
#]
links_data = [
    ("output_data", "input_data"),
    ("output_processed", "input_processed"),
    ("output_analyzed", "input_result"),
]

for output_attr, input_attr in links_data:
    output_node_id = output_attr.split("##")[0]
    input_node_id = input_attr.split("##")[0]
    link_id = random.randint(1, 2**32 - 1)
    links[link_id] = (output_node_id, input_node_id)
    print("Adding node link")
    print("input_node_id: ", input_node_id)
    print("output_node_id: ", output_node_id)
    print(link_id)
    dpg.add_node_link(output_node_id, input_node_id, parent="node_editor", tag=link_id)

dpg.create_viewport(title="Dear PyGui Node Editor Example", width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()

dpg.destroy_context()
