import frappe
from frappe.tests.utils import FrappeTestCase


class TestLeadClassificationFlow(FrappeTestCase):
    """Validate that Lead gets classified before insert and related records after insert."""

    def setUp(self):
        """Initialize test data with a unique phone number."""
        self.phone_number = "099000001"
        self.lead_1 = None
        self.lead_2 = None
        self.contact = None
        self.customer = None

    def tearDown(self):
        """Remove only records created by this test."""
        for record in [self.lead_1, self.lead_2, self.customer]:
            if record:
                frappe.delete_doc_if_exists(record.doctype, record.name, force=True)

        if self.contact:
            frappe.delete_doc_if_exists("Contact", self.contact.name, force=True)

        frappe.db.commit()

    def test_first_lead_classified_as_nuevo(self):
        """A new Lead should include 'Nuevo' but never 'Recurrente'."""
        self.lead_1 = frappe.get_doc({
            "doctype": "Lead",
            "first_name": "First Lead",
            "phone": self.phone_number,
            "custom_person_qty": 3,
            "custom_has_hotel_voucher": 1,
            "is_corpo": 0
        }).insert(ignore_permissions=True)

        frappe.db.commit()
        self.lead_1.reload()

        categories = [row.customer_category for row in self.lead_1.custom_customer_category]

        self.assertIn("Nuevo", categories, "Lead should include 'Nuevo' when no existing Contact.")
        self.assertNotIn("Recurrente", categories, "Lead should not include 'Recurrente' on first creation.")

    def test_first_lead_propagates_classifications_to_contact(self):
        """After insert, the newly created Contact should mirror the Lead classifications."""
        self.lead_1 = frappe.get_doc({
            "doctype": "Lead",
            "first_name": "First Lead",
            "phone": self.phone_number,
            "custom_person_qty": 2,
            "custom_has_hotel_voucher": 1,
            "is_corpo": 1
        }).insert(ignore_permissions=True)

        frappe.db.commit()

        contact_name = frappe.db.get_value("Contact", {"phone": self.phone_number}, "name")
        self.assertTrue(contact_name, "Contact should be created after Lead insert.")

        self.contact = frappe.get_doc("Contact", contact_name).reload()
        lead_categories = {row.customer_category for row in self.lead_1.custom_customer_category}
        contact_categories = {row.customer_category for row in self.contact.custom_customer_category}

        # Contact should exactly mirror Lead classifications
        self.assertSetEqual(
            contact_categories,
            lead_categories,
            f"Contact categories {contact_categories} should match Lead {lead_categories}"
        )

    def test_second_lead_classified_as_recurrente_and_updates_contact_and_customer(self):
        """The second Lead for an existing phone should classify all related docs as only Recurrente."""
        self.lead_1 = frappe.get_doc({
            "doctype": "Lead",
            "first_name": "First Lead",
            "phone": self.phone_number
        }).insert(ignore_permissions=True)
        frappe.db.commit()

        contact_name = frappe.db.get_value("Contact", {"phone": self.phone_number}, "name")
        self.assertTrue(contact_name, "Contact should exist after first Lead insertion")
        self.contact = frappe.get_doc("Contact", contact_name)

        self.customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": "Test Customer",
            "customer_primary_contact": self.contact.name
        }).insert(ignore_permissions=True)
        frappe.db.commit()

        self.lead_2 = frappe.get_doc({
            "doctype": "Lead",
            "first_name": "Second Lead",
            "phone": self.phone_number
        }).insert(ignore_permissions=True)
        frappe.db.commit()

        self.lead_2.reload()
        self.contact.reload()
        self.customer.reload()

        lead2_categories = [row.customer_category for row in self.lead_2.custom_customer_category]
        contact_categories = [row.customer_category for row in self.contact.custom_customer_category]
        customer_categories = [row.customer_category for row in self.customer.custom_customer_category]

        self.assertEqual(lead2_categories, ["Recurrente"], "Lead should have only 'Recurrente' after contact exists")
        self.assertEqual(contact_categories, ["Recurrente"], "Contact should have only 'Recurrente'")
        self.assertEqual(customer_categories, ["Recurrente"], "Customer should have only 'Recurrente'")
