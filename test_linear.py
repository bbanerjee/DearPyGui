import dearpygui.dearpygui as dpg

pipeline_data = [
    {"name": "Data Input", "input_values": [0.0, 0.0]},
    {"name": "Preprocessing", "scale_factor": 1.0},
    {"name": "Analysis", "perform_advanced": False},
    {"name": "Post-processing", "output_format": 0, "output_formats": ["CSV", "TXT", "JSON"]},
    {"name": "Results", "output_value": 0.0},
]

def process_step(step_data):
    name = step_data["name"]
    if name == "Data Input":
        return sum(step_data["input_values"]) * 2.0
    elif name == "Preprocessing":
        if "input_from_previous" in step_data:
            return step_data["input_from_previous"] * step_data["scale_factor"]
        return 0.0
    elif name == "Analysis":
        if "input_from_previous" in step_data:
            return step_data["input_from_previous"] + (5.0 if step_data["perform_advanced"] else 1.0)
        return 0.0
    elif name == "Post-processing":
        if "input_from_previous" in step_data:
            return f"Processed Value (Format: {step_data['output_formats'][step_data['output_format']]}): {step_data['input_from_previous']:.2f}"
        return ""
    elif name == "Results":
        return step_data.get("input_from_previous", 0.0)
    return 0.0

def run_analysis():
    previous_output = None
    for i in range(len(pipeline_data)):
        step = pipeline_data[i]
        if i > 0 and previous_output is not None:
            step["input_from_previous"] = previous_output

        result = process_step(step)
        pipeline_data[i]["output_value"] = result
        previous_output = result

        # Update the UI to show the output
        results_group = dpg.get_item_children(f"step_{len(pipeline_data) - 1}", 1)
        if results_group:
            dpg.configure_item(results_group[0], default_value=f"Output of the previous step: {result}")

    dpg.set_value("analysis_output_text", f"Final Result: {previous_output}")

def update_input_value(sender, app_data, user_data):
    step_index, input_index = user_data
    pipeline_data[step_index]["input_values"][input_index] = app_data

def update_scale_factor(sender, app_data, user_data):
    step_index = user_data
    pipeline_data[step_index]["scale_factor"] = app_data

def update_advanced_analysis(sender, app_data, user_data):
    step_index = user_data
    pipeline_data[step_index]["perform_advanced"] = app_data

def update_output_format(sender, app_data, user_data):
    step_index = user_data
    pipeline_data[step_index]["output_format"] = app_data

def add_input_field(sender, app_data, user_data):
    step_index = user_data
    current_count = len(pipeline_data[step_index]["input_values"])
    dpg.add_input_float(label=f"Input Value {current_count + 1}", default_value=0.0, parent=sender,
                        callback=update_input_value, user_data=(step_index, current_count))
    pipeline_data[step_index]["input_values"].append(0.0)

dpg.create_context()
dpg.create_viewport(title="Dear PyGui Linear Workflow Example", width=450, height=500)
dpg.setup_dearpygui()

with dpg.window(label="Engineering Analysis Pipeline", width=400):
    for i in range(len(pipeline_data)):
        step = pipeline_data[i]
        #with dpg.group(label=step["name"], tag=f"step_{i}", collapsed=False):
        with dpg.collapsing_header(label=step["name"], tag=f"step_{i}", default_open=True): # Use collap
            dpg.add_text(step["name"], tag=f"header_{i}")
            #dpg.push_indent()
            if step["name"] == "Data Input":
                for j, value in enumerate(step["input_values"]):
                    dpg.add_input_float(label=f"Input Value {j + 1}", default_value=value,
                                        callback=update_input_value, user_data=(i, j))
                dpg.add_button(label="Add Input", callback=add_input_field, user_data=i)
            elif step["name"] == "Preprocessing":
                dpg.add_slider_float(label="Scale Factor", default_value=step.get("scale_factor", 1.0), min_value=0.1, max_value=5.0,
                                    callback=update_scale_factor, user_data=i)
            elif step["name"] == "Analysis":
                dpg.add_checkbox(label="Perform advanced analysis", default_value=step.get("perform_advanced", False),
                                callback=update_advanced_analysis, user_data=i)
            elif step["name"] == "Post-processing":
                dpg.add_combo(label="Output Format", items=step["output_formats"], default_value=step.get("output_format", step["output_formats"][0]),
                              callback=update_output_format, user_data=i)
            elif step["name"] == "Results":
                dpg.add_text(f"Output of the previous step: {step['output_value']}", tag=f"results_output_{i}")
            if i < len(pipeline_data) - 1:
                dpg.add_separator()

    dpg.add_button(label="Run Analysis", callback=run_analysis)
    dpg.add_text("", tag="analysis_output_text")

dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
