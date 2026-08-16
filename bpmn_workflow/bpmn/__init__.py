# -*- coding: utf-8 -*-
"""
Generate BPMN 2.0 XML from a flat list of workflow steps.

The XML contains only the BPMN *semantic* model (definitions, process, flow
nodes, sequence flows and one lane per role) - no BPMNDI (coordinates / layout)
information. Layout is computed at render time by the ``bpmn-auto-layout``
library in the browser, so the Python side never has to reason about geometry.

Each step is described by:
    - name        (str)   step name, used as a unique reference
    - next_steps  (list)  names of the steps that follow this one
    - step_type   (str)   "Funktion" (task) or "Abzweigung" (gateway); rows of
                          type "Abzweigung" that share the same step name become
                          branches of one exclusive gateway
    - bedingung   (str)   condition for a gateway row (rendered on the
                          outgoing sequence flow); not allowed for tasks
    - assigned_to (str)   BPMN role that executes the step; every role gets
                          its own horizontal swimlane (lane) in the diagram
    - tool        (str)   tool used to implement the step (stored in documentation)
"""
import re
import xml.etree.ElementTree as ET

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
BPMNDI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
DC_NS = "http://www.omg.org/spec/DD/20100524/DC"
DI_NS = "http://www.omg.org/spec/DD/20100524/DI"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

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


def generate_bpmn_xml(step_records):
	"""step_records: list of dicts
	{name, next_steps (list of str), step_type, bedingung, assigned_to, tool}.

	Returns BPMN 2.0 XML containing only the semantic model (no BPMNDI).
	"""
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
				"step_type": (record.get("step_type") or "Funktion").strip(),
				"bedingung": (record.get("bedingung") or "").strip(),
				"assigned_to": (record.get("assigned_to") or "").strip() or DEFAULT_ROLE,
				"tool": (record.get("tool") or "").strip(),
			}
		)

	existing_names = {step["name"] for step in clean_steps}

	def is_gateway(name):
		return any(
			step["name"] == name and step["step_type"] == "Abzweigung" for step in clean_steps
		)

	pred_map = {}
	for step in clean_steps:
		next_steps = [n for n in step["next_steps"] if n in existing_names]
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

	# Ordered unique step names: first appearance decides the node order
	ordered_names = []
	for step in clean_steps:
		if step["name"] not in ordered_names:
			ordered_names.append(step["name"])

	name_to_id = {}
	for name in ordered_names:
		if is_gateway(name):
			node_id = _unique("Gateway_" + _slugify(name), set(name_to_id.values()))
			name_to_id[name] = node_id
			gateway = ET.SubElement(process, "{" + BPMN_NS + "}exclusiveGateway")
			gateway.set("id", node_id)
			gateway.set("name", name)
		else:
			step = next(s for s in clean_steps if s["name"] == name)
			node_id = _unique("Task_" + _slugify(name), set(name_to_id.values()))
			name_to_id[name] = node_id
			task = ET.SubElement(process, "{" + BPMN_NS + "}userTask")
			task.set("id", node_id)
			task.set("name", name)
			documentation = ET.SubElement(task, "{" + BPMN_NS + "}documentation")
			documentation.set("textFormat", "text/plain")
			documentation.text = "Rolle: {0} | Tool: {1}".format(
				step["assigned_to"] or "-", step["tool"] or "-"
			)

	end_event = ET.SubElement(process, "{" + BPMN_NS + "}endEvent")
	end_event.set("id", "EndEvent_1")
	end_event.set("name", "End")

	# Sequence flows
	flow_id = 0

	def add_flow(source_id, target_id, flow_name=None):
		nonlocal flow_id
		flow_id += 1
		flow = ET.SubElement(process, "{" + BPMN_NS + "}sequenceFlow")
		flow.set("id", "Flow_{0}".format(flow_id))
		flow.set("sourceRef", source_id)
		flow.set("targetRef", target_id)
		if flow_name:
			flow.set("name", flow_name)

	if not clean_steps:
		add_flow("StartEvent_1", "EndEvent_1")
	else:
		for step in clean_steps:
			source_id = name_to_id[step["name"]]
			next_steps = [n for n in step["next_steps"] if n in existing_names]
			if not next_steps:
				add_flow(source_id, "EndEvent_1", flow_name=step.get("bedingung"))
			for nxt in next_steps:
				add_flow(source_id, name_to_id[nxt], flow_name=step.get("bedingung"))
		for name in ordered_names:
			if not pred_map.get(name):
				add_flow("StartEvent_1", name_to_id[name])

	# Lanes: one lane per role, in order of first appearance
	if clean_steps:
		# A gateway has no role of its own; it sits in the lane of the
		# function (step) that calls it. Fall back to DEFAULT_ROLE if none.
		calling_role = {}
		for step in clean_steps:
			if is_gateway(step["name"]):
				continue
			for nxt in step["next_steps"]:
				if nxt in existing_names and is_gateway(nxt):
					calling_role.setdefault(nxt, step["assigned_to"])

		node_role = {}
		for step in clean_steps:
			name = step["name"]
			if is_gateway(name):
				node_role.setdefault(name, calling_role.get(name) or DEFAULT_ROLE)
			else:
				node_role.setdefault(name, step["assigned_to"])

		roles = []
		for step in clean_steps:
			role = node_role[step["name"]]
			if role not in roles:
				roles.append(role)

		# Start/End events belong to the lane of the first/last step
		start_lane = node_role[clean_steps[0]["name"]]
		end_lane = node_role[clean_steps[-1]["name"]]

		lane_set = ET.SubElement(process, "{" + BPMN_NS + "}laneSet")
		lane_set.set("id", "LaneSet_1")
		for index, role in enumerate(roles):
			lane = ET.SubElement(lane_set, "{" + BPMN_NS + "}lane")
			lane.set("id", "Lane_{0}".format(index + 1))
			lane.set("name", role)
			node_ids = [name_to_id[name] for name in ordered_names if node_role.get(name) == role]
			if role == start_lane:
				node_ids.insert(0, "StartEvent_1")
			if role == end_lane:
				node_ids.append("EndEvent_1")
			for node_id in node_ids:
				ref = ET.SubElement(lane, "{" + BPMN_NS + "}flowNodeRef")
				ref.text = node_id

	return ET.tostring(root, encoding="unicode", xml_declaration=True)