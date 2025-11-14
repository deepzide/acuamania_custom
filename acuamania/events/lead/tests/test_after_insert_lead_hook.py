import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import random_string

CUSTOM_CONTACT_LINK_FIELD = "custom_contact_name"


class TestLeadContactCreation(FrappeTestCase):
    """Validate automatic Contact creation and reuse from Lead."""

    def setUp(self):
        frappe.db.rollback()
        self.created_docs = []

    def tearDown(self):
        """Remove only records created in this test (safe cleanup)."""
        for doctype, name in self.created_docs:
            if frappe.db.exists(doctype, name):
                try:
                    frappe.delete_doc(doctype, name, force=True)
                except Exception as e:
                    frappe.log_error(
                        f"Error deleting {doctype} {name}: {e}",
                        "TestLeadContactCreation Cleanup Error"
                    )
        frappe.db.commit()

    def test_contact_created_when_lead_inserted(self):
        """A Contact should be created automatically from a new Lead."""
        frappe.logger("test_lead_contact").info("--- test_contact_created_when_lead_inserted ---")
        print("\n[DEBUG] --- test_contact_created_when_lead_inserted ---")

        unique_email = f"alice_{random_string(6)}@example.com"

        lead = frappe.get_doc({
            "doctype": "Lead",
            "first_name": "Alice",
            "phone": "099111222",
            "email_id": unique_email,
        }).insert(ignore_permissions=True)
        self.created_docs.append(("Lead", lead.name))

        contact_name = (
            frappe.db.get_value("Contact", {"phone": "099111222"}, "name")
            or frappe.db.get_value("Contact", {"custom_phone": "099111222"}, "name")
        )

        frappe.logger("test_lead_contact").info(f"Lead created: {lead.name} ({unique_email})")
        frappe.logger("test_lead_contact").info(f"Linked Contact: {contact_name}")

        print(f"[DEBUG] Lead name: {lead.name}")
        print(f"[DEBUG] Contact created name: {contact_name}")

        self.assertTrue(contact_name, "Contact should have been created automatically from Lead.")
        self.created_docs.append(("Contact", contact_name))

    def test_existing_contact_reused(self):
        """If a Lead with same phone exists, reuse existing Contact."""
        frappe.logger("test_lead_contact").info("--- test_existing_contact_reused ---")
        print("\n[DEBUG] --- test_existing_contact_reused ---")

        first_email = f"alice_{random_string(6)}@example.com"
        second_email = f"alice2_{random_string(6)}@example.com"

        # Create first lead → creates contact
        first_lead = frappe.get_doc({
            "doctype": "Lead",
            "first_name": "Alice",
            "phone": "088888888",
            "email_id": first_email,
        }).insert(ignore_permissions=True)
        self.created_docs.append(("Lead", first_lead.name))

        first_contact_name = frappe.db.get_value("Contact", {"phone": "088888888"}, "name")
        print(f"[DEBUG] First Lead name: {first_lead.name}")
        print(f"[DEBUG] First Contact name: {first_contact_name}")

        self.assertTrue(first_contact_name, "First Contact should have been created.")
        self.created_docs.append(("Contact", first_contact_name))

        # Create second lead → should reuse same contact
        second_lead = frappe.get_doc({
            "doctype": "Lead",
            "first_name": "Alice",
            "phone": "088888888",
            "email_id": second_email,
        }).insert(ignore_permissions=True)
        self.created_docs.append(("Lead", second_lead.name))

        reused_contact_name = second_lead.get(CUSTOM_CONTACT_LINK_FIELD)
        print(f"[DEBUG] Second Lead name: {second_lead.name}")
        print(f"[DEBUG] Second Lead linked contact: {reused_contact_name}")
        print(f"[DEBUG] Expected reused contact: {first_contact_name}")

        frappe.logger("test_lead_contact").info(
            f"Second Lead {second_lead.name} linked contact: {reused_contact_name}"
        )

        self.assertEqual(
            reused_contact_name,
            first_contact_name,
            "Second Lead should reuse the existing Contact with same phone."
        )
