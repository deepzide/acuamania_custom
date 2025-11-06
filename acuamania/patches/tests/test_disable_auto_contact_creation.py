import frappe
import unittest
from acuamania.patches import disable_auto_contact_creation as patch

DOCTYPE = "CRM Settings"


class TestDisableAutoContactCreation(unittest.TestCase):
    def setUp(self):
        frappe.db.rollback()
        self.settings = frappe.get_single(DOCTYPE)
        self.settings.auto_creation_of_contact = 1
        self.settings.save(ignore_permissions=True)
        frappe.db.commit()

    def tearDown(self):
        frappe.db.rollback()

    def test_patch_disables_auto_contact_creation(self):
        patch.execute()
        crm_settings = frappe.get_single(DOCTYPE)
        self.assertEqual(crm_settings.auto_creation_of_contact, 0)
