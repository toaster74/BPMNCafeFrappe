app_name = "bpmn_workflow"
app_title = "BPMN Workflow"
app_publisher = "Frappe Developer"
app_description = "Workflow management app that stores workflows as BPMN 2.0 models and renders them graphically with bpmn-js."
app_email = "dev@example.com"
app_license = "MIT"
app_version = "1.0.0"
app_icon = "octicon octicon-workflow"

# Apps under "/" (public) are served from the app's public folder.
app_include_js = []
app_include_css = []

# Automatically include doctype-specific JS files.
doctype_js = {
	"BPMN Workflow": "public/js/bpmn_workflow.js",
}

# Override methods called from other apps / list of methods available on the
# current document.
doc_events = {}

# Email Notification
notification_config = {}

# Fixtures
fixtures = []

# Custom fields
custom_fields = {}

# Modules (autoload all doctypes from a module)
def get_modules():
	return ["BPMN Workflow"]

# Whitelisted (public) methods that can be called from the client.
override_whitelisted_methods = {}

# Global search (list view) configurations
website_route_rules = []

# Methods in the standard pages you may override (website, web, etc.)
website_route_rules = []

# Links / Permissions
has_website_permission = {}
