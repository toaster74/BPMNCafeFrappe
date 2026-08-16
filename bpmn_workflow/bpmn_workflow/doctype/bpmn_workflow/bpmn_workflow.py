# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

import frappe
from frappe.model.document import Document

from bpmn_workflow.bpmn import generate_bpmn_xml


class BPMNWorkflow(Document):
	def validate(self):
		self.bpmn_xml = generate_bpmn_xml(_step_records(self))

	def on_trash(self):
		pass


@frappe.whitelist()
def get_generated_bpmn(step_records):
	"""Generate a BPMN 2.0 XML for preview purposes, without saving the document."""
	if isinstance(step_records, str):
		step_records = json.loads(step_records)
	return generate_bpmn_xml(step_records)


def _step_records(workflow):
	records = []
	for step in workflow.steps:
		records.append(
			{
				"name": step.step_name,
				"next_steps": _split_next_steps(step.next_step),
				"assigned_to": step.assigned_to,
				"tool": step.tool,
			}
		)
	return records


def _split_next_steps(value):
	"""Split a comma-separated list of step names into a clean list."""
	if not value:
		return []
	return [part.strip() for part in value.split(",") if part.strip()]
