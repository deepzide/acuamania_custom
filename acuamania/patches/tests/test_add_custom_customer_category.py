import frappe
import unittest
from acuamania.patches.custom_fields import add_custom_customer_category as patch

FIELDNAME = "custom_customer_category"
LABEL = "Customer Category"
FIELD_TYPE = "Table MultiSelect"
OPTIONS = "Customer__Customer_Category"
INSERT_AFTER = "customer_name"
TARGET_DOCTYPES = ["Customer", "Contact"]


class TestAddCustomerCategoryField(unittest.TestCase):
    def setUp(self):
        frappe.db.rollback()
        for doctype in TARGET_DOCTYPES:
            frappe.db.delete("Custom Field", {"dt": doctype, "fieldname": FIELDNAME})
        frappe.db.commit()

    def tearDown(self):
        frappe.db.rollback()

    def test_patch_creates_fields_in_all_doctypes(self):
        patch.execute()
        for doctype in TARGET_DOCTYPES:
            exists = frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": FIELDNAME})
            print(doctype, exists)
            self.assertTrue(exists)
            custom_field = frappe.get_doc("Custom Field", exists)
            self.assertEqual(custom_field.label, LABEL)
            self.assertEqual(custom_field.fieldtype, FIELD_TYPE)
            self.assertEqual(custom_field.options, OPTIONS)
            self.assertEqual(custom_field.insert_after, INSERT_AFTER)

    def test_patch_is_idempotent(self):
        patch.execute()
        for doctype in TARGET_DOCTYPES:
            count_before = frappe.db.count("Custom Field", {"dt": doctype, "fieldname": FIELDNAME})
            patch.execute()
            count_after = frappe.db.count("Custom Field", {"dt": doctype, "fieldname": FIELDNAME})
            self.assertEqual(count_before, count_after)
