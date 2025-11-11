import frappe
import logging
import sys
import os
from frappe.tests.utils import FrappeTestCase


class TestNormalizeContactPhone(FrappeTestCase):
    """Validate that Contact.before_save normalizes phone and custom_phone in real workflows."""

    @classmethod
    def setUpClass(cls):
        """Initialize custom logger that logs to both stdout and file."""
        # Ensure log directory exists
        site_name = frappe.local.site or frappe.get_site_path().split(os.sep)[-2]
        log_dir = frappe.get_site_path("logs")
        os.makedirs(log_dir, exist_ok=True)

        log_path = os.path.join(log_dir, "test_normalize_contact_phone.log")

        # Create logger
        cls.logger = logging.getLogger("test_normalize_contact_phone")
        cls.logger.setLevel(logging.INFO)

        # Console handler (prints in bench run-tests output)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter("[%(levelname)s] %(message)s")
        console_handler.setFormatter(console_format)

        # File handler (saves into logs folder)
        file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_format = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        file_handler.setFormatter(file_format)

        # Attach both handlers
        cls.logger.addHandler(console_handler)
        cls.logger.addHandler(file_handler)
        cls.logger.propagate = False

        cls.logger.info("🧪 Starting TestNormalizeContactPhone suite...")
        cls.logger.info(f"📂 Log file: {log_path}")

    def tearDown(self):
        self.logger.info("🧹 Cleaning up test data...")
        for doc in getattr(self, "_created_docs", []):
            if frappe.db.exists(doc.doctype, doc.name):
                frappe.delete_doc(doc.doctype, doc.name, force=True)
        frappe.db.commit()
        self.logger.info("✅ Cleanup complete.")

    def test_user_created_contact_from_ui(self):
        """Simulate user creating a Contact manually filling custom_phone."""
        self.logger.info("📱 Creating Contact manually (UI simulation)...")

        contact_data = {
            "doctype": "Contact",
            "first_name": "Alice",
            "last_name": "Doe",
            "email_id": "alice@example.com",
            "custom_phone": "099111222",
        }
        self.logger.info(f"➡️ Contact payload: {contact_data}")

        contact = frappe.get_doc(contact_data).insert(ignore_permissions=True)
        self.logger.info(f"✅ Contact inserted: {contact.name}")

        contact.reload()
        self.logger.info(
            f"🔁 Reloaded Contact: phone={contact.phone}, custom_phone={contact.custom_phone}"
        )

        self.assertEqual(
            contact.phone,
            "099111222",
            "Phone should be set from custom_phone when Contact is created manually."
        )
        self.logger.info("✅ Assertion passed: phone normalized correctly.")

    def test_contact_created_from_lead(self):
        """Simulate ERPNext lead creation which auto-creates a Contact with phone but no custom_phone."""
        self.logger.info("🧩 Creating Lead to trigger Contact auto-creation...")

        lead_data = {
            "doctype": "Lead",
            "first_name": "Test Lead",
            "email_id": "lead@example.com",
            "phone": "088888888",
        }
        self.logger.info(f"➡️ Lead payload: {lead_data}")

        lead = frappe.get_doc(lead_data).insert(ignore_permissions=True)
        self.logger.info(f"✅ Lead inserted: {lead.name} (phone={lead.phone})")

        frappe.db.commit()
        self.logger.info("💾 DB committed after Lead insertion.")

        contact_names = frappe.get_all("Contact", filters={"phone": "088888888"}, pluck="name")
        self.logger.info(f"🔍 Contacts found by phone='088888888': {contact_names}")

        self.assertTrue(contact_names, "Contact should have been auto-created from Lead.")

        contact = frappe.get_doc("Contact", contact_names[0])
        self.logger.info(
            f"📞 Loaded Contact doc: name={contact.name}, phone={contact.phone}, custom_phone={contact.custom_phone}"
        )

        self.assertEqual(
            contact.custom_phone,
            "088888888",
            "Custom phone should be set from phone when Contact is created from Lead."
        )
        self.logger.info("✅ Assertion passed: custom_phone propagated correctly from phone.")
