import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today
from acuamania.events.contact.contact_propagation.contact_propagation import contact_propagation


class TestContactPropagation(FrappeTestCase):
    """Validate that Contact propagation hook updates related doctypes correctly."""

    @classmethod
    def setUpClass(cls):
        cls.logger = frappe.logger("test_contact_propagation")
        cls.logger.info("🧪 Starting Contact propagation tests...")

        if not frappe.db.exists("Item Group", {"item_group_name": "Test Group"}):
            frappe.get_doc({
                "doctype": "Item Group",
                "item_group_name": "Test Group",
                "is_group": 0,
                "parent_item_group": "All Item Groups"
            }).insert(ignore_permissions=True)
            frappe.db.commit()

        if not frappe.db.exists("Item", {"item_code": "Test Item"}):
            frappe.get_doc({
                "doctype": "Item",
                "item_code": "Test Item",
                "item_name": "Test Item",
                "is_stock_item": 0,
                "item_group": "Test Group"
            }).insert(ignore_permissions=True)
            frappe.db.commit()

    def setUp(self):
        frappe.db.rollback()
        self.logger.info("🔧 Setting up Contact and related doctypes...")

        self.contact = frappe.get_doc({
            "doctype": "Contact",
            "first_name": "Alice",
            "last_name": "Doe",
            "email_id": "alice@example.com",
            "custom_phone": "099111222",
            "custom_source": "WhatsApp",
            "custom_territory": {"name": "Paysandú"},
        }).insert(ignore_permissions=True)

        self.logger.info(f"✅ Contact created: {self.contact.name}")

        self.lead = frappe.get_doc({
            "doctype": "Lead",
            "first_name": "Old",
            "last_name": "Value",
            "phone": self.contact.custom_phone,
            "email_id": "old@example.com",
            "source": "",
            "territory": "",
        }).insert(ignore_permissions=True)

        self.logger.info(f"✅ Lead created: {self.lead.name} (phone={self.lead.phone})")

        self.opportunity = frappe.get_doc({
            "doctype": "Opportunity",
            "opportunity_from": "Lead",
            "party_name": self.lead.name,
            "phone": self.contact.custom_phone,
            "contact_email": "",
            "territory": "",
        }).insert(ignore_permissions=True)

        self.customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": "Test Customer",
            "mobile_no": self.contact.custom_phone,
            "email_id": "old_customer@example.com",
            "custom_source": "",
            "territory": "",
        }).insert(ignore_permissions=True)

        try:
            self.contact = frappe.get_doc("Contact", self.contact.name)
            self.contact.append("links", {
                "link_doctype": "Customer",
                "link_name": self.customer.name
            })
            self.contact.save(ignore_permissions=True)
            frappe.db.commit()
        except frappe.TimestampMismatchError:
            self.logger.warning("⚠️ Contact modified by hook; reloading and retrying save.")
            self.contact.reload()
            if not any(l.link_name == self.customer.name for l in self.contact.links):
                self.contact.append("links", {
                    "link_doctype": "Customer",
                    "link_name": self.customer.name
                })
                self.contact.save(ignore_permissions=True)
                frappe.db.commit()

        self.sales_order = frappe.get_doc({
            "doctype": "Sales Order",
            "customer": self.customer.name,
            "contact_person": self.contact.name,
            "transaction_date": today(),
            "custom_email": "",
            "territory": "",
            "custom_source": "",
            "docstatus": 0,
            "grand_total": 100.0,
            "items": [
                {
                    "item_code": "Test Item",
                    "qty": 1,
                    "rate": 100.0,
                    "delivery_date": today(),
                }
            ],
        }).insert(ignore_permissions=True)

        frappe.db.commit()
        self.logger.info("✅ Test data setup completed.")

    def tearDown(self):
        self.logger.info("🧹 Cleaning up test data...")

        doctypes_to_clean = ["Sales Order", "Opportunity", "Lead", "Customer", "Contact"]
        for doctype in doctypes_to_clean:
            try:
                names = frappe.get_all(doctype, filters={"phone": "099111222"}, pluck="name")
                names += frappe.get_all(doctype, filters={"mobile_no": "099111222"}, pluck="name")
                for name in names:
                    frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
                    self.logger.info(f"🗑️ Deleted {doctype} {name}")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not delete some {doctype}: {e}")

        frappe.db.commit()
        self.logger.info("✅ Cleanup completed safely.")

    def test_contact_field_propagation(self):
        """Ensure propagation hook updates linked doctypes as expected."""
        self.logger.info("🚀 Running contact propagation test...")

        self.contact.reload()
        self.contact.custom_source = "Instagram"
        self.contact.custom_territory = "Paysandú"
        self.contact.custom_email = "newalice@example.com"
        self.contact.save(ignore_permissions=True)

        self.logger.info(
            f"✏️ Contact updated: source={self.contact.custom_source}, territory={self.contact.custom_territory}"
        )

        contact_propagation(self.contact, "after_save")
        self.logger.info("🔄 Propagation hook executed manually.")

        self.lead.reload()
        self.opportunity.reload()
        self.sales_order.reload()
        self.customer.reload()

        self.assertEqual(self.lead.source, "Instagram")
        self.assertEqual(self.lead.territory, "Paysandú")
        self.assertEqual(self.lead.email_id, "newalice@example.com")

        self.assertEqual(self.opportunity.contact_email, "newalice@example.com")
        self.assertEqual(self.opportunity.territory, "Paysandú")

        self.assertEqual(self.sales_order.custom_email, "newalice@example.com")
        self.assertEqual(self.sales_order.source, "Instagram")
        self.assertEqual(self.sales_order.territory, "Paysandú")

        self.assertEqual(self.customer.territory, "Paysandú")
        self.assertEqual(self.customer.email_id, "newalice@example.com")

        self.logger.info("✅ All propagation assertions passed successfully.")
