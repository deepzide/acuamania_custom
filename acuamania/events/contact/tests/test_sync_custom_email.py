import frappe
import logging
import sys
import os
from frappe.tests.utils import FrappeTestCase


class TestSyncCustomEmail(FrappeTestCase):
    """Validate that Contact.custom_email automatically syncs to email_id on before_save."""

    @classmethod
    def setUpClass(cls):
        """Initialize custom logger (stdout + file)."""
        log_dir = frappe.get_site_path("logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "test_sync_custom_email.log")

        cls.logger = logging.getLogger("test_sync_custom_email")
        cls.logger.setLevel(logging.INFO)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

        file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

        cls.logger.addHandler(console_handler)
        cls.logger.addHandler(file_handler)
        cls.logger.propagate = False

        cls.logger.info("🧪 Starting TestSyncCustomEmail suite...")
        cls.logger.info(f"📂 Log file: {log_path}")

    def setUp(self):
        frappe.db.rollback()
        self.logger.info("🔧 Setting up new Contact...")

    def tearDown(self):
        """Safely delete created Contact."""
        self.logger.info("🧹 Cleaning up test data...")
        for name in frappe.get_all("Contact", filters={"first_name": "Email Test"}, pluck="name"):
            frappe.delete_doc("Contact", name, force=True, ignore_permissions=True)
        frappe.db.commit()
        self.logger.info("✅ Cleanup completed.")

    def test_custom_email_syncs_to_email_id(self):
        """Ensure that before_save hook updates email_id from custom_email."""
        self.logger.info("🚀 Running automatic sync test...")

        contact = frappe.get_doc({
            "doctype": "Contact",
            "first_name": "Email Test",
            "custom_email": "hooked_email@example.com"
        }).insert(ignore_permissions=True)

        self.logger.info(f"✅ Contact inserted: {contact.name}")
        self.logger.info(f"🔍 Values → custom_email={contact.custom_email}, email_id={contact.email_id}")

        contact.reload()

        self.assertEqual(
            contact.email_id,
            "hooked_email@example.com",
            "email_id should automatically sync from custom_email on save."
        )

        self.logger.info("✅ Hook executed successfully and email_id was updated.")
