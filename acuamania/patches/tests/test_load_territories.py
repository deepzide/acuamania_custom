import json
import os

import frappe
from frappe.tests.utils import FrappeTestCase

from acuamania.patches import load_territories


class TestAddTerritoriesNomenclator(FrappeTestCase):
	"""Validate that load_territories patch loads JSON correctly and creates all territories."""

	@classmethod
	def setUpClass(cls):
		"""Load JSON data once for all tests."""
		app_path = frappe.get_app_path("acuamania")
		json_path = os.path.join(app_path, "nomenclators", "territories.json")

		with open(json_path, encoding="utf-8") as json_file:
			cls.territories_data = json.load(json_file)

	def test_patch_creates_territories_from_json(self):
		"""Run the patch and verify all territories from JSON exist after execution."""
		load_territories.execute()

		for entry in self.territories_data:
			exists = frappe.db.exists("Territory", {"territory_name": entry["territory_name"]})
			self.assertTrue(
				exists, f"Territory '{entry['territory_name']}' should exist after patch execution."
			)

	def test_parent_territory_defaults_to_all(self):
		"""Verify all created territories have parent territory 'All Territories'."""
		load_territories.execute()

		for entry in self.territories_data:
			parent_territory = frappe.db.get_value(
				"Territory", {"territory_name": entry["territory_name"]}, "parent_territory"
			)
			self.assertEqual(
				parent_territory,
				"All Territories",
				f"Parent territory should default to 'All Territories' for {entry['territory_name']}.",
			)

	def test_patch_is_idempotent(self):
		"""Run the patch twice to confirm no duplicates are created."""
		load_territories.execute()
		first_counts = self._get_territory_counts()
		load_territories.execute()
		second_counts = self._get_territory_counts()
		self.assertEqual(
			first_counts, second_counts, "Patch should be idempotent and not duplicate territories."
		)

	def _get_territory_counts(self):
		"""Return the number of Territory records created per name."""
		counts = {}
		for entry in self.territories_data:
			count = frappe.db.count("Territory", {"territory_name": entry["territory_name"]})
			counts[entry["territory_name"]] = count
		return counts
