import json

import frappe

DOCTYPE = "Territory"
FILE_PATH = frappe.get_app_path("acuamania", "nomenclators", "territories.json")


def load_nomenclator(file_path):
	"""Load Territory records from JSON."""
	with open(file_path, encoding="utf-8") as f:
		return json.load(f)


def record_exists(doctype, territory_name):
	"""Check if a Territory with the same name already exists."""
	return frappe.db.exists(doctype, {"territory_name": territory_name})


def create_record(entry):
	"""Create a new Territory record."""
	doc = frappe.new_doc(DOCTYPE)
	doc.territory_name = entry.get("territory_name")
	doc.custom_is_resident = entry.get("custom_is_resident", 0)
	doc.parent_territory = entry.get("parent_territory", "All Territories")
	doc.save(ignore_permissions=True)


def execute():
	"""Patch entry point for loading Uruguay territories."""
	try:
		nomenclator = load_nomenclator(FILE_PATH)

		for entry in nomenclator:
			if not record_exists(DOCTYPE, entry["territory_name"]):
				create_record(entry)

		frappe.db.commit()
		frappe.logger().info(
			f"✅ Nomenclator '{DOCTYPE}' loaded successfully with {len(nomenclator)} records."
		)

	except Exception as e:
		frappe.log_error(message=str(e), title=f"{DOCTYPE} Sync Failed")
