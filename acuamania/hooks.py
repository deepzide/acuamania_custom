app_name = "acuamania"
app_title = "Acuamania"
app_publisher = "cegomezpy"
app_description = "Acuamania App"
app_email = "cegomezpy@gmail.com"
app_license = "unlicense"


fixtures = [
    # {"dt": "Item"},
    {"dt": "Park Promotion"},
    {"dt": "Lead"},
    {"dt": "Opportunity"},
    {"dt": "Quotation"},
    {"dt": "Sales Order"},
    {
        "dt": "Workspace",
        "filters": [["name", "in", ["Acuamania Analytics"]]],
    },
    {
        "dt": "Number Card",
        "filters": [
            [
                "name",
                "in",
                [
                    "Leads (30d)",
                    "Oportunidades (30d)",
                    "Cotizaciones (30d)",
                    "Ordenes de Venta (30d)",
                ],
            ]
        ],
    },
    {
        "dt": "Report",
        "filters": [["name", "in", ["Embudo Comercial Acuamania"]]],
    },
]


# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "acuamania",
# 		"logo": "/assets/acuamania/logo.png",
# 		"title": "Acuamania",
# 		"route": "/acuamania",
# 		"has_permission": "acuamania.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/acuamania/css/acuamania.css"
# app_include_js = "/assets/acuamania/js/acuamania.js"

# include js, css files in header of web template
# web_include_css = "/assets/acuamania/css/acuamania.css"
# web_include_js = "/assets/acuamania/js/acuamania.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "acuamania/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "acuamania/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "acuamania.utils.jinja_methods",
# 	"filters": "acuamania.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "acuamania.install.before_install"
# after_install = "acuamania.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "acuamania.uninstall.before_uninstall"
# after_uninstall = "acuamania.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "acuamania.utils.before_app_install"
# after_app_install = "acuamania.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "acuamania.utils.before_app_uninstall"
# after_app_uninstall = "acuamania.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "acuamania.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Lead": {
        "validate": "acuamania.validations.lead.validate_lead.validate_lead",
        "on_update": "acuamania.events.lead.on_update.on_update",
        "after_insert": "acuamania.events.lead.after_insert.after_insert",
        "before_insert": "acuamania.events.lead.before_insert.before_insert",
        "before_save": "acuamania.events.lead.before_save.before_save",
    },
    "Contact": {
        "before_save": "acuamania.events.contact.before_save.before_save",
        "on_update": "acuamania.events.contact.on_update.on_update",
        "before_insert": "acuamania.events.contact.before_insert.before_insert",
    },
    "Sales Order": {
        "before_save": "acuamania.events.sales_order.before_save.before_save",
        "on_submit": "acuamania.events.sales_order.on_submit.on_submit",
    },
    "Quotation": {
        "before_save": "acuamania.events.quotation.before_save.before_save",
    },
}


# Scheduled Tasks
# ---------------

scheduler_events = {
	# "all": [
	# 	"acuamania.tasks.all"
	# ],
	"daily": [
		"acuamania.tasks.daily.save_transcriptions.save_transcriptions"
	],
	# "hourly": [
	# 	"acuamania.tasks.hourly"
	# ],
	# "weekly": [
	# 	"acuamania.tasks.weekly"
	# ],
	# "monthly": [
	# 	"acuamania.tasks.monthly"
	# ],
}

# Testing
# -------

# before_tests = "acuamania.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "acuamania.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "acuamania.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["acuamania.utils.before_request"]
# after_request = ["acuamania.utils.after_request"]

# Job Events
# ----------
# before_job = ["acuamania.utils.before_job"]
# after_job = ["acuamania.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"acuamania.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
