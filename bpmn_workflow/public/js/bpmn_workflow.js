// Client-side logic for the "BPMN Workflow" DocType.
// Renders the generated BPMN 2.0 model in the form using bpmn-js.
// Layout (DI coordinates) is computed at render time by bpmn-auto-layout.

var BPMN_ASSETS = [
	"/assets/bpmn_workflow/css/vendor/diagram-js.css",
	"/assets/bpmn_workflow/css/vendor/bpmn-js.css",
	"/assets/bpmn_workflow/css/vendor/bpmn-embedded.css",
	"/assets/bpmn_workflow/js/bpmn-auto-layout/bpmn-auto-layout.min.js",
	"/assets/bpmn_workflow/js/bpmn-js/bpmn-viewer.production.min.js",
];

var PDF_ASSETS = ["/assets/bpmn_workflow/js/bpmn-pdf/bpmn-pdf.min.js"];

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

		frappe
			.call({
				method: "bpmn_workflow.bpmn_workflow.doctype.bpmn_workflow.bpmn_workflow.get_generated_bpmn",
				args: { step_records: step_records },
			})
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

	// Triggered by the "PDF Export" button (field option "pdf_export").
	// Exports the currently rendered BPMN diagram as a PDF download.
	pdf_export: function (frm) {
		if (!frm.bpmn_viewer) {
			frappe.msgprint({
				title: __("No Diagram"),
				message: __("Generate the BPMN diagram first."),
				indicator: "orange",
			});
			return;
		}
		frappe.require(PDF_ASSETS).then(function () {
			export_bpmn_pdf(frm);
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
	if (!window.BpmnJS || !window.BpmnAutoLayout) return;

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

	// Compute layout (DI) client-side from the semantic model
	BpmnAutoLayout.layoutProcess(xml)
		.then(function (result) {
			var layouted_xml = typeof result === "string" ? result : result.xml;
			return render_viewer(frm, layouted_xml);
		})
		.catch(function (err) {
			console.error(err);
			frappe.msgprint({
				title: __("Error"),
				message: __("Could not compute the BPMN layout."),
				indicator: "red",
			});
		});
}

function render_viewer(frm, xml) {
	if (frm.bpmn_viewer) {
		frm.bpmn_viewer.destroy();
		frm.bpmn_viewer = null;
	}

	var container = document.getElementById("bpmn-preview-container");
	container.innerHTML = "";

	var viewer = new BpmnJS({
		container: container,
		height: "100%",
	});

	return viewer
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
}

function export_bpmn_pdf(frm) {
	var viewer = frm.bpmn_viewer;
	if (!viewer) return;

	frappe.show_alert({ message: __("Preparing PDF..."), indicator: "blue" });

	viewer
		.saveSVG()
		.then(function (result) {
			var svg = result.svg;
			var container = document.createElement("div");
			container.style.position = "absolute";
			container.style.left = "-9999px";
			container.style.top = "0";
			container.style.width = "100px";
			container.style.height = "100px";
			document.body.appendChild(container);
			container.innerHTML = svg;

			var svgElement = container.querySelector("svg");
			var bounds = svgElement.getBoundingClientRect();
			var svgWidth = bounds.width || 800;
			var svgHeight = bounds.height || 600;

			var pdf = new window.BPMNPDF.jsPDF({
				orientation: "landscape",
				unit: "pt",
				format: "a4",
			});

			var pageWidth = pdf.internal.pageSize.getWidth();
			var pageHeight = pdf.internal.pageSize.getHeight();
			var margin = 30;

			var scale = Math.min(
				(pageWidth - margin * 2) / svgWidth,
				(pageHeight - margin * 2) / svgHeight
			);

			var x = (pageWidth - svgWidth * scale) / 2;
			var y = (pageHeight - svgHeight * scale) / 2;

			window.BPMNPDF.svg2pdf(svgElement, pdf, {
				x: x,
				y: y,
				width: svgWidth * scale,
				height: svgHeight * scale,
			});

			var filename = (frm.doc.workflow_name || "bpmn-workflow") + ".pdf";
			pdf.save(filename);

			document.body.removeChild(container);
			frappe.show_alert({ message: __("PDF exported."), indicator: "green" });
		})
		.catch(function (err) {
			console.error(err);
			frappe.msgprint({
				title: __("Error"),
				message: __("Could not export the PDF."),
				indicator: "red",
			});
		});
}