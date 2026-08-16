// Client-side logic for the "BPMN Workflow" DocType.
// Renders the generated BPMN 2.0 model in the form using bpmn-js.

var BPMN_ASSETS = [
	"/assets/bpmn_workflow/css/vendor/diagram-js.css",
	"/assets/bpmn_workflow/css/vendor/bpmn-js.css",
	"/assets/bpmn_workflow/css/vendor/bpmn-embedded.css",
	"/assets/bpmn_workflow/js/bpmn-js/bpmn-viewer.production.min.js",
];

frappe.ui.form.on("BPMN Workflow", {
	refresh: function (frm) {
		load_bpmn_assets(function () {
			frm.bpmn_assets_loaded = true;
			render_bpmn_diagram(frm);
		});
	},

	after_save: function (frm) {
		if (frm.bpmn_assets_loaded) {
			render_bpmn_diagram(frm);
		}
	},

	// Triggered by the "Generate BPMN Model" button (field option "generate_bpmn").
	// Generates the XML on the server and renders it without saving the document.
	generate_bpmn: function (frm) {
		var step_records = (frm.doc.steps || []).map(function (step) {
			var next_steps = (step.next_step || "")
				.split(",")
				.map(function (part) {
					return part.trim();
				})
				.filter(Boolean);
			return {
				name: step.step_name,
				next_steps: next_steps,
				assigned_to: step.assigned_to,
				tool: step.tool,
			};
		});

		frm
			.call("get_generated_bpmn", { step_records: step_records })
			.then(function (r) {
				if (r.message) {
					frm.set_value("bpmn_xml", r.message);
					frm.refresh_field("bpmn_xml");
					if (frm.bpmn_assets_loaded) {
						render_bpmn_diagram(frm);
					}
				}
			});
	},
});

function load_bpmn_assets(callback) {
	if (window.BpmnJS) {
		callback();
		return;
	}
	frappe.require(BPMN_ASSETS).then(callback);
}

function render_bpmn_diagram(frm) {
	if (!window.BpmnJS) return;

	var container = document.getElementById("bpmn-preview-container");
	if (!container) return;

	var xml = frm.doc.bpmn_xml;
	if (!xml) {
		container.innerHTML =
			'<p class="text-muted" style="padding:30px;text-align:center;">' +
			__("Add workflow steps and click 'Generate BPMN Model' to render the diagram.") +
			"</p>";
		return;
	}

	if (frm.bpmn_viewer) {
		frm.bpmn_viewer.destroy();
		frm.bpmn_viewer = null;
	}

	container.innerHTML = "";

	var viewer = new BpmnJS({
		container: container,
		height: "100%",
	});

	viewer
		.importXML(xml)
		.then(function () {
			var canvas = viewer.get("canvas");
			canvas.zoom("fit-viewport", "auto");
		})
		.catch(function (err) {
			console.error(err);
			frappe.msgprint({
				title: __("Error"),
				message: __("Could not render the BPMN diagram."),
				indicator: "red",
			});
		});

	frm.bpmn_viewer = viewer;
}
