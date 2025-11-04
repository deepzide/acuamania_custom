import frappe
import unittest
from acuamania.patches import load_lead_sources as patch

DOCTYPE = "Lead Source"
FILE_PATH = frappe.get_app_path("acuamania", "nomenclators", "lead_sources.json")


class TestLoadLeadSources(unittest.TestCase):
    def setUp(self):
        frappe.db.rollback()
        self.data = patch.load_nomenclator(FILE_PATH)
        frappe.db.delete(DOCTYPE)
        frappe.db.commit()

    def tearDown(self):
        frappe.db.rollback()

    def test_patch_creates_all_sources(self):
        patch.execute()
        for entry in self.data:
            exists = frappe.db.exists(DOCTYPE, {"source_name": entry["source_name"]})
            self.assertTrue(exists)

    def test_patch_is_idempotent(self):
        patch.execute()
        count_before = frappe.db.count(DOCTYPE)
        patch.execute()
        count_after = frappe.db.count(DOCTYPE)
        self.assertEqual(count_before, count_after)
