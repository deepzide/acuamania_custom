import frappe
from frappe.tests.utils import FrappeTestCase


class TestBeforeInsertLeadHook(FrappeTestCase):
    """Validate that before_insert hook classifies Lead, Contact, and Customer correctly."""

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
        """The first Lead for a new phone should be classified only as Nuevo."""
        self.lead_1 = frappe.get_doc({
            "doctype": "Lead",
            "lead_name": "First Lead",
            "phone": self.phone_number
        }).insert(ignore_permissions=True)

        categories = [row.customer_category for row in self.lead_1.custom_customer_category]
        self.assertEqual(categories, ["Nuevo"], "Lead should have only 'Nuevo' category on first insertion")

    def test_second_lead_classified_as_recurrente_and_updates_contact_and_customer(self):
        """The second Lead for an existing phone should classify all related docs as only Recurrente."""
        self.lead_1 = frappe.get_doc({
            "doctype": "Lead",
            "lead_name": "First Lead",
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
            "lead_name": "Second Lead",
            "phone": self.phone_number
        }).insert(ignore_permissions=True)

        lead2_categories = [row.customer_category for row in self.lead_2.custom_customer_category]
        contact_categories = [row.customer_category for row in self.contact.reload().custom_customer_category]
        customer_categories = [row.customer_category for row in self.customer.reload().custom_customer_category]

        self.assertEqual(lead2_categories, ["Recurrente"], "Lead should have only 'Recurrente' after contact exists")
        self.assertEqual(contact_categories, ["Recurrente"], "Contact should have only 'Recurrente'")
        self.assertEqual(customer_categories, ["Recurrente"], "Customer should have only 'Recurrente'")
