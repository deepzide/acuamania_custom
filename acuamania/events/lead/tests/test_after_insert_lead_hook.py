import frappe
import unittest
from frappe.exceptions import ValidationError

LEAD_DOCTYPE = "Lead"
CONTACT_DOCTYPE = "Contact"
CUSTOM_CONTACT_LINK_FIELD = "custom_contact_name"


class TestLeadContactCreation(unittest.TestCase):
    def setUp(self):
        frappe.db.rollback()
        self.phone_number = "099999999"
        self.email = "lead_test@example.com"
        frappe.db.delete(LEAD_DOCTYPE, {"phone": self.phone_number})
        frappe.db.delete(CONTACT_DOCTYPE, {"phone": self.phone_number})
        frappe.db.commit()


    def tearDown(self):
        frappe.db.rollback()


    def test_contact_created_when_lead_inserted(self):
        lead = frappe.get_doc({
            "doctype": LEAD_DOCTYPE,
            "first_name": "Auto Contact Lead",
            "phone": self.phone_number,
            "email_id": self.email
        })
        lead.insert(ignore_permissions=True)
        contact_name = frappe.db.exists(CONTACT_DOCTYPE, {"phone": self.phone_number})
        self.assertTrue(contact_name)
        lead.reload()
        self.assertEqual(lead.get(CUSTOM_CONTACT_LINK_FIELD), contact_name)


    def test_existing_contact_reused(self):
        first_lead = frappe.get_doc({
            "doctype": LEAD_DOCTYPE,
            "first_name": "First Lead",
            "phone": self.phone_number,
            "email_id": "first@example.com"
        })
        first_lead.insert(ignore_permissions=True)
        first_lead.reload()
        first_contact_name = first_lead.get(CUSTOM_CONTACT_LINK_FIELD)
        self.assertTrue(first_contact_name)

        second_lead = frappe.get_doc({
            "doctype": LEAD_DOCTYPE,
            "first_name": "Second Lead",
            "phone": self.phone_number,
            "email_id": "second@example.com"
        })
        second_lead.insert(ignore_permissions=True)
        second_lead.reload()

        self.assertEqual(second_lead.get(CUSTOM_CONTACT_LINK_FIELD), first_contact_name)

        contacts_with_phone = frappe.get_all(
            CONTACT_DOCTYPE,
            filters={"phone": self.phone_number},
            pluck="name"
        )
        self.assertEqual(len(contacts_with_phone), 1)


    def test_lead_without_phone_raises_error(self):
        with self.assertRaises(ValidationError):
            frappe.get_doc({
                "doctype": LEAD_DOCTYPE,
                "first_name": "No Phone Lead"
            }).insert(ignore_permissions=True)
