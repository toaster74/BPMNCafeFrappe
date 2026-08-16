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
				step_type: step.step_type,
				bedingung: step.bedingung,
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

// Plausibility check for each step row entered in the child table.
frappe.ui.form.on("BPMN Workflow Step", {
	validate: function (frm, cdt, cdn) {
		var row = frappe.get_doc(cdt, cdn);
		var step_type = (row.step_type || "Funktion").trim();
		var bedingung = (row.bedingung || "").trim();
		var assigned_to = (row.assigned_to || "").trim();
		if (step_type === "Abzweigung" && !bedingung) {
			frappe.throw(
				__("Step '{0}': a condition (Bedingung) is required for a gateway (Abzweigung).").format(
					row.step_name
				)
			);
		}
		if (step_type === "Abzweigung" && assigned_to) {
			frappe.throw(
				__("Step '{0}': a gateway (Abzweigung) must not have a role (Rolle).").format(
					row.step_name
				)
			);
		}
		if (step_type === "Funktion" && bedingung) {
			frappe.throw(
				__(
					"Step '{0}': a condition (Bedingung) is not allowed for a function (Funktion)."
				).format(row.step_name)
			);
		}
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

	inject_viewer_css();
	build_toolbar(frm, container);

	var canvas = document.createElement("div");
	canvas.className = "bpmn-canvas";
	container.appendChild(canvas);

	var viewer = new BpmnJS({
		container: canvas,
		height: "100%",
	});

	frm.bpmn_viewer = viewer;
	active_viewer = viewer;
	active_container = container;

	return viewer
		.importXML(xml)
		.then(function () {
			var canvas_view = viewer.get("canvas");
			canvas_view.zoom("fit-viewport", "auto");
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

var active_viewer = null;
var active_container = null;

function inject_viewer_css() {
	if (document.getElementById("bpmn-viewer-css")) return;
	var style = document.createElement("style");
	style.id = "bpmn-viewer-css";
	style.textContent = [
		"#bpmn-preview-container{position:relative;}",
		"#bpmn-preview-container .bpmn-canvas{position:absolute;top:0;left:0;right:0;bottom:0;}",
		"#bpmn-preview-container .bpmn-toolbar{position:absolute;top:8px;right:8px;z-index:100;display:flex;gap:4px;padding:4px;background:rgba(255,255,255,.92);border:1px solid var(--border-color);border-radius:6px;box-shadow:0 1px 3px rgba(0,0,0,.1);}",
		"#bpmn-preview-container .bpmn-btn{border:1px solid var(--border-color);background:#fff;color:inherit;border-radius:4px;cursor:pointer;padding:2px 8px;font-size:13px;line-height:1.5;}",
		"#bpmn-preview-container .bpmn-btn:hover{background:var(--control-bg);}",
	].join("\n");
	document.head.appendChild(style);
}

function build_toolbar(frm, container) {
	var toolbar = document.createElement("div");
	toolbar.className = "bpmn-toolbar";
	toolbar.innerHTML =
		'<button type="button" class="bpmn-btn" data-action="zoom-out" title="Zoom Out">-</button>' +
		'<button type="button" class="bpmn-btn" data-action="zoom-in" title="Zoom In">+</button>' +
		'<button type="button" class="bpmn-btn" data-action="fit" title="Fit to Screen">Fit</button>' +
		'<button type="button" class="bpmn-btn" data-action="fullscreen" title="Toggle Fullscreen">&#10530;</button>';
	container.appendChild(toolbar);

	toolbar.addEventListener("click", function (event) {
		var btn = event.target.closest(".bpmn-btn");
		if (!btn || !frm.bpmn_viewer) return;
		var canvas = frm.bpmn_viewer.get("canvas");
		switch (btn.dataset.action) {
			case "zoom-in":
				canvas.zoom(1.25);
				break;
			case "zoom-out":
				canvas.zoom(0.8);
				break;
			case "fit":
				canvas.zoom("fit-viewport", "auto");
				break;
			case "fullscreen":
				toggle_fullscreen(container);
				break;
		}
	});
}

function toggle_fullscreen(container) {
	var doc = container.ownerDocument;
	if (!doc.fullscreenElement) {
		if (container.requestFullscreen) {
			container.requestFullscreen();
		} else if (container.webkitRequestFullscreen) {
			container.webkitRequestFullscreen();
		}
	} else {
		if (doc.exitFullscreen) {
			doc.exitFullscreen();
		} else if (doc.webkitExitFullscreen) {
			doc.webkitExitFullscreen();
		}
	}
}

document.addEventListener("fullscreenchange", function () {
	// Re-fit after the fullscreen container has been resized.
	if (document.fullscreenElement && active_viewer) {
		setTimeout(function () {
			active_viewer.get("canvas").zoom("fit-viewport", "auto");
		}, 100);
	}
});

function export_bpmn_pdf(frm) {
	var viewer = frm.bpmn_viewer;
	if (!viewer) return;

	frappe.show_alert({ message: __("Preparing PDF..."), indicator: "blue" });

	viewer
		.saveSVG()
		.then(function (result) {
			return svg_to_canvas(result.svg);
		})
		.then(function (canvas) {
			var pdf = new window.BPMNPDF.jsPDF({
				orientation: "landscape",
				unit: "pt",
				format: "a4",
			});

			var pageWidth = pdf.internal.pageSize.getWidth();
			var pageHeight = pdf.internal.pageSize.getHeight();
			var margin = 30;

			var imgWidth = canvas.width;
			var imgHeight = canvas.height;

			var scale = Math.min(
				(pageWidth - margin * 2) / imgWidth,
				(pageHeight - margin * 2) / imgHeight
			);

			var w = imgWidth * scale;
			var h = imgHeight * scale;
			var x = (pageWidth - w) / 2;
			var y = (pageHeight - h) / 2;

			pdf.addImage(canvas.toDataURL("image/png"), "PNG", x, y, w, h);

			var filename = (frm.doc.workflow_name || "bpmn-workflow") + ".pdf";
			pdf.save(filename);

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

function svg_to_canvas(svgString) {
	return new Promise(function (resolve, reject) {
		var svg = new DOMParser().parseFromString(svgString, "image/svg+xml").documentElement;

		// Browsers use a default size for SVGs without explicit width/height.
		// Derive the size from the viewBox so the raster is not empty/1px.
		var viewBox = svg.getAttribute("viewBox");
		if (viewBox) {
			var parts = viewBox.split(/[\s,]+/).map(Number);
			if (!svg.getAttribute("width")) {
				svg.setAttribute("width", parts[2]);
			}
			if (!svg.getAttribute("height")) {
				svg.setAttribute("height", parts[3]);
			}
		}

		var dataUrl =
			"data:image/svg+xml;charset=utf-8," +
			encodeURIComponent(new XMLSerializer().serializeToString(svg));

		var image = new Image();
		image.onload = function () {
			var renderScale = 2;
			var canvas = document.createElement("canvas");
			canvas.width = image.width * renderScale;
			canvas.height = image.height * renderScale;
			var ctx = canvas.getContext("2d");
			ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
			resolve(canvas);
		};
		image.onerror = function () {
			reject(new Error("Could not rasterize the BPMN diagram."));
		};
		image.src = dataUrl;
	});
}