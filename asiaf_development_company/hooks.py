app_name = "asiaf_development_company"
app_title = "Asiaf Development Company"
app_publisher = "EnAi Team Development & Research"
app_description = "Asiaf Development Company provides integrated facility management, engineering, and support services in Saudi Arabia, delivering efficient, safe, and customized solutions for businesses and public spaces."
app_email = "fshureih@enarainc.com"
app_license = "mit"
fixtures = [
    {
        "dt": "Client Script"
    },
    {
        "dt": "Server Script"
    },
  
    
]



# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "asiaf_development_company",
# 		"logo": "/assets/asiaf_development_company/logo.png",
# 		"title": "Asiaf Development Company",
# 		"route": "/asiaf_development_company",
# 		"has_permission": "asiaf_development_company.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/asiaf_development_company/css/custom.css?v=6"
# app_include_js = "/assets/asiaf_development_company/js/asiaf_development_company.js"

# include js, css files in header of web template
# web_include_css = "/assets/asiaf_development_company/css/asiaf_development_company.css"
# web_include_js = "/assets/asiaf_development_company/js/asiaf_development_company.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "asiaf_development_company/public/scss/website"

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
# app_include_icons = "asiaf_development_company/public/icons.svg"

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

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "asiaf_development_company.utils.jinja_methods",
# 	"filters": "asiaf_development_company.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "asiaf_development_company.install.before_install"
# after_install = "asiaf_development_company.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "asiaf_development_company.uninstall.before_uninstall"
# after_uninstall = "asiaf_development_company.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "asiaf_development_company.utils.before_app_install"
# after_app_install = "asiaf_development_company.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "asiaf_development_company.utils.before_app_uninstall"
# after_app_uninstall = "asiaf_development_company.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "asiaf_development_company.notifications.get_notification_config"

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

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"asiaf_development_company.tasks.all"
# 	],
# 	"daily": [
# 		"asiaf_development_company.tasks.daily"
# 	],
# 	"hourly": [
# 		"asiaf_development_company.tasks.hourly"
# 	],
# 	"weekly": [
# 		"asiaf_development_company.tasks.weekly"
# 	],
# 	"monthly": [
# 		"asiaf_development_company.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "asiaf_development_company.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "asiaf_development_company.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "asiaf_development_company.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "asiaf_development_company.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["asiaf_development_company.utils.before_request"]
# after_request = ["asiaf_development_company.utils.after_request"]

# Job Events
# ----------
# before_job = ["asiaf_development_company.utils.before_job"]
# after_job = ["asiaf_development_company.utils.after_job"]

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
# 	"asiaf_development_company.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

