import json
import os

import frappe
from frappe.tests.utils import FrappeTestCase

from acuamania.patches import add_custom_fields


class TestAddCustomFieldsPatch(FrappeTestCase):
	"""Validate that add_custom_fields patch loads JSON correctly and creates all fields."""

	def setUp(self):
		"""Load JSON configuration for custom fields."""
		app_path = frappe.get_app_path("acuamania")
		json_path = os.path.join(app_path, "custom_fields", "custom_fields.json")

		with open(json_path, encoding="utf-8") as json_file:
			self.custom_fields_data = json.load(json_file)

		# Clean up any existing custom fields defined in JSON
		for doctype, fields in self.custom_fields_data.items():
			for field in fields:
				frappe.db.delete("Custom Field", {"dt": doctype, "fieldname": field["fieldname"]})
		frappe.db.commit()

	def test_patch_creates_fields_from_json(self):
		"""Run the patch and verify that all fields from JSON exist after execution."""
		add_custom_fields.execute()

		for doctype, fields in self.custom_fields_data.items():
			for field in fields:
				exists = frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field["fieldname"]})
				self.assertTrue(
					exists,
					f"Custom field '{field['fieldname']}' should exist in '{doctype}' after patch execution.",
				)

	def test_field_definitions_are_consistent_with_json(self):
		"""Validate that all fields in the database match their JSON definitions (fieldtype, label)."""
		add_custom_fields.execute()

		for doctype, fields in self.custom_fields_data.items():
			for field in fields:
				db_field = frappe.db.get_value(
					"Custom Field",
					{"dt": doctype, "fieldname": field["fieldname"]},
					["label", "fieldtype", "options"],
					as_dict=True,
				)

				self.assertIsNotNone(db_field, f"Field '{field['fieldname']}' missing in {doctype}.")
				self.assertEqual(
					db_field["label"],
					field.get("label"),
					f"Label mismatch for {field['fieldname']} in {doctype}.",
				)
				self.assertEqual(
					db_field["fieldtype"],
					field.get("fieldtype"),
					f"Fieldtype mismatch for {field['fieldname']} in {doctype}.",
				)

	def test_patch_is_idempotent(self):
		"""Run the patch twice to confirm no duplicate Custom Fields are created."""
		add_custom_fields.execute()
		initial_counts = self._get_field_counts()
		add_custom_fields.execute()
		second_counts = self._get_field_counts()
		self.assertEqual(
			initial_counts, second_counts, "Patch should be idempotent and not duplicate fields."
		)

	def _get_field_counts(self):
		"""Return the number of Custom Fields created per (doctype, fieldname)."""
		counts = {}
		for doctype, fields in self.custom_fields_data.items():
			for field in fields:
				count = frappe.db.count("Custom Field", {"dt": doctype, "fieldname": field["fieldname"]})
				counts[(doctype, field["fieldname"])] = count
		return counts
