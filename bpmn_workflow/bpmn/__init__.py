# -*- coding: utf-8 -*-
"""
Generate BPMN 2.0 XML (including BPMNDI layout information) from a flat list
of workflow steps.

Each step is described by:
    - name        (str)   step name, used as a unique reference
    - next_steps  (list)  names of the steps that follow this one
    - assigned_to (str)   BPMN role that executes the step; every role gets
                          its own horizontal swimlane (lane) in the diagram
    - tool        (str)   tool used to implement the step (stored in documentation)

The generator produces a fully layouted diagram (layered, left-to-right, one
swimlane per role) so that bpmn-js can render it without a manual layout pass.
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
LANE_HEADER_W = 100
LANE_PAD_TOP = 30
LANE_PAD_BOTTOM = 30
LANE_END_MARGIN = 80
DEFAULT_ROLE = "Unassigned"


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


def _group_by_layer(nodes):
	by_layer = {}
	for node in nodes:
		by_layer.setdefault(node["layer"], []).append(node)
	return by_layer


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
				"assigned_to": (record.get("assigned_to") or "").strip() or DEFAULT_ROLE,
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
		documentation.text = "Rolle: {0} | Tool: {1}".format(
			step["assigned_to"] or "-", step["tool"] or "-"
		)
		task_nodes.append(
			{
				"id": node_id,
				"name": step["name"],
				"role": step["assigned_to"],
				"layer": 0,
				"w": TASK_W,
				"h": TASK_H,
			}
		)

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

	# ---- Layout ----
	if not clean_steps:
		add_flow("StartEvent_1", "EndEvent_1")
		nodes = [
			{
				"id": "StartEvent_1",
				"x": LANE_HEADER_W + BASE_X - EVENT_W / 2.0,
				"y": 60.0,
				"w": EVENT_W,
				"h": EVENT_H,
			},
			{
				"id": "EndEvent_1",
				"x": LANE_HEADER_W + BASE_X + COL_W - EVENT_W / 2.0,
				"y": 60.0,
				"w": EVENT_W,
				"h": EVENT_H,
			},
		]
		node_by_id = {node["id"]: node for node in nodes}

		diagram = ET.SubElement(root, "{" + BPMNDI_NS + "}BPMNDiagram")
		diagram.set("id", "BPMNDiagram_1")
		plane = ET.SubElement(diagram, "{" + BPMNDI_NS + "}BPMNPlane")
		plane.set("id", "BPMNPlane_1")
		plane.set("bpmnElement", "Process_1")
		for node in nodes:
			add_shape(plane, node)
		for edge_id, source_id, target_id in flow_records:
			add_edge(plane, edge_id, source_id, target_id, node_by_id)
		return ET.tostring(root, encoding="unicode", xml_declaration=True)

	layer_of = _layer_assignments(
		[step["name"] for step in clean_steps], next_map, pred_map
	)
	for task in task_nodes:
		task["layer"] = layer_of[task["name"]]
	max_layer = max((task["layer"] for task in task_nodes), default=1)

	for step in clean_steps:
		for nxt in next_map[step["name"]]:
			add_flow(name_to_id[step["name"]], name_to_id[nxt])
		if not next_map[step["name"]]:
			add_flow(name_to_id[step["name"]], "EndEvent_1")
	for name in clean_steps:
		if not pred_map.get(name["name"]):
			add_flow("StartEvent_1", name_to_id[name["name"]])

	# Roles -> lanes, in order of first appearance
	roles = []
	for task in task_nodes:
		if task["role"] not in roles:
			roles.append(task["role"])
	lane_index = {role: i for i, role in enumerate(roles)}
	for task in task_nodes:
		task["lane"] = lane_index[task["role"]]

	start_node = {"id": "StartEvent_1", "layer": 0, "w": EVENT_W, "h": EVENT_H}
	end_node = {"id": "EndEvent_1", "layer": max_layer + 1, "w": EVENT_W, "h": EVENT_H}
	start_node["lane"] = task_nodes[0]["lane"]
	end_node["lane"] = task_nodes[-1]["lane"]

	# Collect nodes per lane
	lane_nodes = {i: [] for i in range(len(roles))}
	for task in task_nodes:
		lane_nodes[task["lane"]].append(task)
	lane_nodes[start_node["lane"]].append(start_node)
	lane_nodes[end_node["lane"]].append(end_node)

	# Lane heights
	lane_heights = {}
	for i, nodes in lane_nodes.items():
		by_layer = _group_by_layer(nodes)
		stack = max((len(group) for group in by_layer.values()), default=1)
		lane_heights[i] = LANE_PAD_TOP + stack * ROW_H + LANE_PAD_BOTTOM

	# Lane y offsets
	lane_y = {}
	cursor = 0
	for i in range(len(roles)):
		lane_y[i] = cursor
		cursor += lane_heights[i]

	# Position nodes inside their lanes
	nodes = []
	for i, nodes_in_lane in lane_nodes.items():
		top = lane_y[i]
		height = lane_heights[i]
		for layer, group in _group_by_layer(nodes_in_lane).items():
			stack_h = len(group) * ROW_H
			y_offset = top + (height - stack_h) / 2.0
			for index, node in enumerate(group):
				x_center = LANE_HEADER_W + BASE_X + layer * COL_W
				node["x"] = x_center - node["w"] / 2.0
				node["y"] = y_offset + index * ROW_H - node["h"] / 2.0
				nodes.append(node)

	node_by_id = {node["id"]: node for node in nodes}

	lane_w = max((node["x"] + node["w"] for node in nodes), default=0) + LANE_END_MARGIN

	# ---- Lanes (XML) ----
	lane_set = ET.SubElement(process, "{" + BPMN_NS + "}laneSet")
	lane_set.set("id", "LaneSet_1")
	for i, role in enumerate(roles):
		lane = ET.SubElement(lane_set, "{" + BPMN_NS + "}lane")
		lane.set("id", "Lane_{0}".format(i + 1))
		lane.set("name", role)
		for node in lane_nodes[i]:
			ref = ET.SubElement(lane, "{" + BPMN_NS + "}flowNodeRef")
			ref.text = node["id"]

	# ---- BPMNDI ----
	diagram = ET.SubElement(root, "{" + BPMNDI_NS + "}BPMNDiagram")
	diagram.set("id", "BPMNDiagram_1")
	plane = ET.SubElement(diagram, "{" + BPMNDI_NS + "}BPMNPlane")
	plane.set("id", "BPMNPlane_1")
	plane.set("bpmnElement", "Process_1")

	# Lane shapes
	for i in range(len(roles)):
		shape = ET.SubElement(plane, "{" + BPMNDI_NS + "}BPMNShape")
		shape.set("id", "LaneShape_{0}".format(i + 1))
		shape.set("bpmnElement", "Lane_{0}".format(i + 1))
		shape.set("isHorizontal", "true")
		bounds = ET.SubElement(shape, "{" + DC_NS + "}Bounds")
		bounds.set("x", "0")
		bounds.set("y", "{0:.1f}".format(lane_y[i]))
		bounds.set("width", "{0:.1f}".format(lane_w))
		bounds.set("height", "{0:.1f}".format(lane_heights[i]))

	for node in nodes:
		add_shape(plane, node)

	for edge_id, source_id, target_id in flow_records:
		if source_id not in node_by_id or target_id not in node_by_id:
			continue
		add_edge(plane, edge_id, source_id, target_id, node_by_id)

	return ET.tostring(root, encoding="unicode", xml_declaration=True)


def add_shape(plane, node):
	shape = ET.SubElement(plane, "{" + BPMNDI_NS + "}BPMNShape")
	shape.set("id", "Shape_{0}".format(node["id"]))
	shape.set("bpmnElement", node["id"])
	bounds = ET.SubElement(shape, "{" + DC_NS + "}Bounds")
	bounds.set("x", "{0:.1f}".format(node["x"]))
	bounds.set("y", "{0:.1f}".format(node["y"]))
	bounds.set("width", str(int(node["w"])))
	bounds.set("height", str(int(node["h"])))


def add_edge(plane, edge_id, source_id, target_id, node_by_id):
	edge = ET.SubElement(plane, "{" + BPMNDI_NS + "}BPMNEdge")
	edge.set("id", "Edge_{0}".format(edge_id))
	edge.set("bpmnElement", edge_id)
	source = node_by_id[source_id]
	target = node_by_id[target_id]
	source_point = (source["x"] + source["w"], source["y"] + source["h"] / 2.0)
	target_point = (target["x"], target["y"] + target["h"] / 2.0)
	for px, py in (source_point, target_point):
		waypoint = ET.SubElement(edge, "{" + DI_NS + "}waypoint")
		waypoint.set("x", "{0:.1f}".format(px))
		waypoint.set("y", "{0:.1f}".format(py))