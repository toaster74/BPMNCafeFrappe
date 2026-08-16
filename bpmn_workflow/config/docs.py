# -*- coding: utf-8 -*-
from frappe import _


def get_data():
	return {
		"category": "BPM",
		"description": _(
			"Manage workflows as BPMN 2.0 models. Define steps, their order, "
			"the responsible user and the tool used to implement each step."
		),
		"projects": [],
	}
