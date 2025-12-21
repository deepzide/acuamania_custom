import json
import os

import frappe

from acuamania.utils.custom_field_utils import create_custom_field


def execute():
	"""Create all custom fields for Lead, Contact, and Customer from one JSON file."""
	try:
		all_fields = _load_field_definitions()

		for doctype, fields in all_fields.items():
			for field in fields:
				create_custom_field(field, doctype)

		frappe.db.commit()
		frappe.logger().info("✅ All custom fields created successfully for Lead, Contact, and Customer.")
	except Exception as exc:
		frappe.log_error(
			message=str(exc), title="Failed to create custom fields for Lead, Contact, and Customer"
		)


def _load_field_definitions() -> dict:
	"""Load explicit field definitions from JSON file."""
	app_path = frappe.get_app_path("acuamania")
	json_path = os.path.join(app_path, "custom_fields", "custom_fields.json")

	with open(json_path, encoding="utf-8") as json_file:
		return json.load(json_file)
