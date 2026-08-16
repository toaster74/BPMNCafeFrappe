# -*- coding: utf-8 -*-
"""
Generate BPMN 2.0 XML (including BPMNDI layout information) from a flat list
of workflow steps.

Each step is described by:
    - name        (str)   step name, used as a unique reference
    - next_steps  (list)  names of the steps that follow this one
    - assigned_to (str)   user who executes the step (stored in documentation)
    - tool        (str)   tool used to implement the step (stored in documentation)

The generator produces a fully layouted diagram (layered, left-to-right) so
that bpmn-js can render it without a manual layout pass.
"""
import re
import xml.etree.ElementTree as ET

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
BPMNDI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
DC_NS = "http://www.omg.org/spec/DD/20100524/DC"
DI_NS = "http://www.omg.org/spec/DD/20100524/DI"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

# Layout constants (px)
TASK_W = 150
TASK_H = 80
EVENT_W = 40
EVENT_H = 40
COL_W = 240
ROW_H = 160
BASE_X = 120
BASE_Y = 160


def _register_namespaces():
	ET.register_namespace("bpmn2", BPMN_NS)
	ET.register_namespace("bpmndi", BPMNDI_NS)
	ET.register_namespace("dc", DC_NS)
	ET.register_namespace("di", DI_NS)
	ET.register_namespace("xsi", XSI_NS)


def _slugify(name):
	slug = re.sub(r"[^A-Za-z0-9]+", "_", str(name)).strip("_")
	return slug or "Step"


def _unique(prefix, used):
	candidate = prefix
	counter = 1
	while candidate in used:
		counter += 1
		candidate = "{0}_{1}".format(prefix, counter)
	used.add(candidate)
	return candidate


def _layer_assignments(step_names, next_map, pred_map):
	"""Assign each step a layer (column). Layer 1 is the first column after the
	start event; cycles are bounded so the algorithm always terminates."""
	layer_of = {}
	max_iterations = len(step_names) + 2
	for _ in range(max_iterations):
		changed = False
		for name in step_names:
			predecessors = pred_map.get(name, set())
			if not predecessors:
				target = 1
			else:
				target = max((layer_of.get(p, 0) for p in predecessors), default=0) + 1
			if layer_of.get(name) is None or target > layer_of[name]:
				layer_of[name] = target
				changed = True
		if not changed:
			break
	for name in layer_of:
		layer_of[name] = min(layer_of[name], len(step_names) + 1)
	return layer_of


def _position_nodes(nodes):
	"""Group nodes by layer and assign x/y coordinates. Mutates nodes in place."""
	by_layer = {}
	for node in nodes:
		by_layer.setdefault(node["layer"], []).append(node)
	for layer, layer_nodes in by_layer.items():
		count = len(layer_nodes)
		for index, node in enumerate(layer_nodes):
			x_center = BASE_X + layer * COL_W
			y_center = BASE_Y + (index - (count - 1) / 2.0) * ROW_H
			node["x"] = x_center - node["w"] / 2.0
			node["y"] = y_center - node["h"] / 2.0
	return nodes


def generate_bpmn_xml(step_records):
	"""step_records: list of dicts {name, next_steps (list of str), assigned_to, tool}."""
	_register_namespaces()

	# Normalize input
	clean_steps = []
	for record in step_records or []:
		name = (record.get("name") or "").strip()
		if not name:
			continue
		clean_steps.append(
			{
				"name": name,
				"next_steps": list(record.get("next_steps") or []),
				"assigned_to": (record.get("assigned_to") or "").strip(),
				"tool": (record.get("tool") or "").strip(),
			}
		)

	existing_names = {step["name"] for step in clean_steps}
	next_map = {}
	pred_map = {}
	for step in clean_steps:
		next_steps = [n for n in step["next_steps"] if n in existing_names]
		next_map[step["name"]] = next_steps
		for n in next_steps:
			pred_map.setdefault(n, set()).add(step["name"])

	root = ET.Element("{" + BPMN_NS + "}definitions")
	root.set("id", "Definitions_1")
	root.set("targetNamespace", "http://bpmn.io/schema/bpmn")

	process = ET.SubElement(root, "{" + BPMN_NS + "}process")
	process.set("id", "Process_1")
	process.set("isExecutable", "false")

	start_event = ET.SubElement(process, "{" + BPMN_NS + "}startEvent")
	start_event.set("id", "StartEvent_1")
	start_event.set("name", "Start")

	name_to_id = {}
	task_nodes = []
	for step in clean_steps:
		node_id = _unique("Task_" + _slugify(step["name"]), set(name_to_id.values()))
		name_to_id[step["name"]] = node_id
		task = ET.SubElement(process, "{" + BPMN_NS + "}userTask")
		task.set("id", node_id)
		task.set("name", step["name"])
		documentation = ET.SubElement(task, "{" + BPMN_NS + "}documentation")
		documentation.set("textFormat", "text/plain")
		documentation.text = "Executor: {0} | Tool: {1}".format(
			step["assigned_to"] or "-", step["tool"] or "-"
		)
		task_nodes.append({"id": node_id, "name": step["name"], "layer": 0, "w": TASK_W, "h": TASK_H})

	end_event = ET.SubElement(process, "{" + BPMN_NS + "}endEvent")
	end_event.set("id", "EndEvent_1")
	end_event.set("name", "End")

	# Sequence flows
	flow_records = []
	flow_id = 0

	def add_flow(source_id, target_id):
		nonlocal flow_id
		flow_id += 1
		flow = ET.SubElement(process, "{" + BPMN_NS + "}sequenceFlow")
		flow.set("id", "Flow_{0}".format(flow_id))
		flow.set("sourceRef", source_id)
		flow.set("targetRef", target_id)
		flow_records.append(("Flow_{0}".format(flow_id), source_id, target_id))

	if not clean_steps:
		add_flow("StartEvent_1", "EndEvent_1")
	else:
		for step in clean_steps:
			for nxt in next_map[step["name"]]:
				add_flow(name_to_id[step["name"]], name_to_id[nxt])
			if not next_map[step["name"]]:
				add_flow(name_to_id[step["name"]], "EndEvent_1")
		for name in clean_steps:
			if not pred_map.get(name["name"]):
				add_flow("StartEvent_1", name_to_id[name["name"]])

	# ---- Layout ----
	layer_of = _layer_assignments(
		[step["name"] for step in clean_steps], next_map, pred_map
	)
	for task in task_nodes:
		task["layer"] = layer_of[task["name"]]
	max_layer = max((task["layer"] for task in task_nodes), default=1)

	all_nodes = [{"id": "StartEvent_1", "layer": 0, "w": EVENT_W, "h": EVENT_H}]
	all_nodes += task_nodes
	all_nodes += [{"id": "EndEvent_1", "layer": max_layer + 1, "w": EVENT_W, "h": EVENT_H}]
	_position_nodes(all_nodes)

	node_by_id = {node["id"]: node for node in all_nodes}

	# ---- BPMNDI ----
	diagram = ET.SubElement(root, "{" + BPMNDI_NS + "}BPMNDiagram")
	diagram.set("id", "BPMNDiagram_1")
	plane = ET.SubElement(diagram, "{" + BPMNDI_NS + "}BPMNPlane")
	plane.set("id", "BPMNPlane_1")
	plane.set("bpmnElement", "Process_1")

	def add_shape(node_id, x, y, w, h):
		shape = ET.SubElement(plane, "{" + BPMNDI_NS + "}BPMNShape")
		shape.set("id", "Shape_{0}".format(node_id))
		shape.set("bpmnElement", node_id)
		bounds = ET.SubElement(shape, "{" + DC_NS + "}Bounds")
		bounds.set("x", "{0:.1f}".format(x))
		bounds.set("y", "{0:.1f}".format(y))
		bounds.set("width", str(int(w)))
		bounds.set("height", str(int(h)))

	def add_edge(edge_id, source_id, target_id, source_point, target_point):
		edge = ET.SubElement(plane, "{" + BPMNDI_NS + "}BPMNEdge")
		edge.set("id", "Edge_{0}".format(edge_id))
		edge.set("bpmnElement", edge_id)
		for px, py in (source_point, target_point):
			waypoint = ET.SubElement(edge, "{" + DI_NS + "}waypoint")
			waypoint.set("x", "{0:.1f}".format(px))
			waypoint.set("y", "{0:.1f}".format(py))

	for node in all_nodes:
		add_shape(node["id"], node["x"], node["y"], node["w"], node["h"])

	for edge_id, source_id, target_id in flow_records:
		if source_id not in node_by_id or target_id not in node_by_id:
			continue
		source = node_by_id[source_id]
		target = node_by_id[target_id]
		source_point = (source["x"] + source["w"], source["y"] + source["h"] / 2.0)
		target_point = (target["x"], target["y"] + target["h"] / 2.0)
		add_edge(edge_id, source_id, target_id, source_point, target_point)

	return ET.tostring(root, encoding="unicode", xml_declaration=True)
