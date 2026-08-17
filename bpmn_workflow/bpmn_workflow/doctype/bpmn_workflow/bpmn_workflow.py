# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

import frappe
from frappe.model.document import Document

from bpmn_workflow.bpmn import generate_bpmn_xml


class BPMNWorkflow(Document):
	def validate(self):
		_validate_steps(self.steps)
		self.bpmn_xml = generate_bpmn_xml(_step_records(self))
		self.collapsed_xml = self.bpmn_xml if self.bpmn_xml else ""

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
				"step_type": step.step_type,
				"bedingung": step.bedingung,
				"assigned_to": step.assigned_to,
				"tool": step.tool,
			}
		)
	return records


def _validate_steps(steps):
	"""Plausibility check for each step row.

	- A step of type "Abzweigung" (gateway) must have a condition.
	- A step of type "Abzweigung" (gateway) must NOT have a role.
	- A step of type "Funktion" (task) must NOT have a condition.
	"""
	for step in steps:
		name = (step.step_name or "").strip()
		step_type = (step.step_type or "Funktion").strip()
		bedingung = (step.bedingung or "").strip()
		assigned_to = (step.assigned_to or "").strip()
		if step_type == "Abzweigung" and not bedingung:
			frappe.throw(
				frappe._("Step '{0}': a condition (Bedingung) is required for a gateway (Abzweigung).").format(
					name
				)
			)
		if step_type == "Abzweigung" and assigned_to:
			frappe.throw(
				frappe._(
					"Step '{0}': a gateway (Abzweigung) must not have a role (Rolle)."
				).format(name)
			)
		if step_type == "Funktion" and bedingung:
			frappe.throw(
				frappe._(
					"Step '{0}': a condition (Bedingung) is not allowed for a function (Funktion)."
				).format(name)
			)


def _split_next_steps(value):
	"""Split a comma-separated list of step names into a clean list."""
	if not value:
		return []
	return [part.strip() for part in value.split(",") if part.strip()]
