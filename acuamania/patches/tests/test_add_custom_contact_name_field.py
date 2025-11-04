import frappe
import unittest
from acuamania.patches.custom_fields import add_lead_custom_contact_name as patch

LEAD_DOCTYPE = "Lead"
FIELDNAME = "custom_contact_name"
FIELD_LABEL = "Contact Name"
FIELD_TYPE = "Link"
FIELD_OPTIONS = "Contact"

class TestAddCustomContactNameField(unittest.TestCase):
    def setUp(self):
        frappe.db.rollback()
        frappe.db.delete("Custom Field", {"dt": LEAD_DOCTYPE, "fieldname": FIELDNAME})
        frappe.db.commit()

    def tearDown(self):
        frappe.db.rollback()

    def test_patch_creates_custom_field(self):
        patch.execute()
        exists = frappe.db.exists("Custom Field", {"dt": LEAD_DOCTYPE, "fieldname": FIELDNAME})
        self.assertTrue(exists)
        custom_field = frappe.get_doc("Custom Field", exists)
        self.assertEqual(custom_field.label, FIELD_LABEL)
        self.assertEqual(custom_field.fieldtype, FIELD_TYPE)
        self.assertEqual(custom_field.options, FIELD_OPTIONS)

    def test_patch_is_idempotent(self):
        patch.execute()
        count_before = frappe.db.count("Custom Field", {"dt": LEAD_DOCTYPE, "fieldname": FIELDNAME})
        patch.execute()
        count_after = frappe.db.count("Custom Field", {"dt": LEAD_DOCTYPE, "fieldname": FIELDNAME})
        self.assertEqual(count_before, count_after)
