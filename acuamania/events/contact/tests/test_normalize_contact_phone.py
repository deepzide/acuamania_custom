import frappe
import logging
import sys
import os
import random
import string
from frappe.tests.utils import FrappeTestCase


# ----------------------------------------------------------------------
# CONSTANTS
# ----------------------------------------------------------------------

LOG_NAME = "test_normalize_contact_phone"
LOG_FILENAME = "test_normalize_contact_phone.log"

RANDOM_EMAIL_DOMAIN = "test.com"
RANDOM_EMAIL_LENGTH = 5

TEST_CONTACT_FIRST_NAME = "Alice"
TEST_CONTACT_LAST_NAME = "Doe"
TEST_CONTACT_PHONE = "099111222"

TEST_LEAD_FIRST_NAME = "Test Lead"
TEST_LEAD_PHONE = "088888888"


# ----------------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------------

def random_email():
    """Return a randomized email using N lowercase letters."""
    local = ''.join(random.choices(string.ascii_lowercase, k=RANDOM_EMAIL_LENGTH))
    return f"{local}@{RANDOM_EMAIL_DOMAIN}"


# ----------------------------------------------------------------------
# TEST SUITE
# ----------------------------------------------------------------------

class TestNormalizeContactPhone(FrappeTestCase):
    """Validate that Contact.before_save normalizes phone and custom_phone in real workflows."""

    @classmethod
    def setUpClass(cls):
        """Initialize custom logger that logs to both stdout and file."""
        site_name = frappe.local.site or frappe.get_site_path().split(os.sep)[-2]
        log_dir = frappe.get_site_path("logs")
        os.makedirs(log_dir, exist_ok=True)

        log_path = os.path.join(log_dir, LOG_FILENAME)

        cls.logger = logging.getLogger(LOG_NAME)
        cls.logger.setLevel(logging.INFO)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

        file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

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

    # ------------------------------------------------------------------
    # TEST 1: Contact manually created from UI
    # ------------------------------------------------------------------

    def test_user_created_contact_from_ui(self):
        """Simulate user creating a Contact manually filling custom_phone."""
        self.logger.info("📱 Creating Contact manually (UI simulation)...")

        contact_data = {
            "doctype": "Contact",
            "first_name": TEST_CONTACT_FIRST_NAME,
            "last_name": TEST_CONTACT_LAST_NAME,
            "email_id": random_email(),               # <-- Random email
            "custom_phone": TEST_CONTACT_PHONE,
        }
        self.logger.info(f"➡️ Contact payload: {contact_data}")

        contact = frappe.get_doc(contact_data).insert(ignore_permissions=True)
        self.logger.info(f"✅ Contact inserted: {contact.name}")

        # Track created docs for cleanup
        self._created_docs = getattr(self, "_created_docs", []) + [contact]

        contact.reload()
        self.logger.info(
            f"🔁 Reloaded Contact: phone={contact.phone}, custom_phone={contact.custom_phone}"
        )

        self.assertEqual(
            contact.phone,
            TEST_CONTACT_PHONE,
            "Phone should be set from custom_phone when Contact is created manually."
        )
        self.logger.info("✅ Assertion passed: phone normalized correctly.")

    # ------------------------------------------------------------------
    # TEST 2: Contact auto-created from Lead
    # ------------------------------------------------------------------

    def test_contact_created_from_lead(self):
        """Simulate ERPNext lead creation which auto-creates a Contact with phone but no custom_phone."""
        self.logger.info("🧩 Creating Lead to trigger Contact auto-creation...")

        lead_data = {
            "doctype": "Lead",
            "first_name": TEST_LEAD_FIRST_NAME,
            "email_id": random_email(),               # <-- Random email
            "phone": TEST_LEAD_PHONE,
        }

        self.logger.info(f"➡️ Lead payload: {lead_data}")

        lead = frappe.get_doc(lead_data).insert(ignore_permissions=True)
        self.logger.info(f"✅ Lead inserted: {lead.name} (phone={lead.phone})")

        self._created_docs = getattr(self, "_created_docs", []) + [lead]

        frappe.db.commit()
        self.logger.info("💾 DB committed after Lead insertion.")

        contact_names = frappe.get_all("Contact", filters={"phone": TEST_LEAD_PHONE}, pluck="name")
        self.logger.info(f"🔍 Contacts found by phone='{TEST_LEAD_PHONE}': {contact_names}")

        self.assertTrue(contact_names, "Contact should have been auto-created from Lead.")

        contact = frappe.get_doc("Contact", contact_names[0])
        self.logger.info(
            f"📞 Loaded Contact doc: name={contact.name}, phone={contact.phone}, custom_phone={contact.custom_phone}"
        )

        self.assertEqual(
            contact.custom_phone,
            TEST_LEAD_PHONE,
            "Custom phone should be set from phone when Contact is created from Lead."
        )
        self.logger.info("✅ Assertion passed: custom_phone propagated correctly from phone.")
