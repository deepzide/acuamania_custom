import frappe
import os
from frappe.tests.utils import FrappeTestCase

CRON = "acuamania.tasks.daily.save_transcriptions.save_transcriptions"


class TestSaveTranscriptions(FrappeTestCase):

    def setUp(self):
        # Create a contact with pending transcription buffer
        self.contact = frappe.get_doc({
            "doctype": "Contact",
            "first_name": "Cron Tester",
            "phone_nos": [{"phone": "098765432"}],
            "custom_transcription_text": "Linea 1\nLinea 2"
        }).insert(ignore_permissions=True)

        self.cron = frappe.get_attr(CRON)
        self.today = frappe.utils.nowdate()

    def test_cron_exports_and_clears_buffer(self):
        # Run cron job
        self.cron()

        # Reload contact
        c = frappe.get_doc("Contact", self.contact.name)

        # 1) Buffer must be cleared
        self.assertEqual(c.custom_transcription_text, "")

        # 2) A File DocType must exist
        filename = f"TRS-{self.contact.name}-{self.today}.txt"
        expected_url = f"/private/files/{filename}"

        file_doc_name = frappe.db.get_value("File", {"file_url": expected_url}, "name")
        self.assertIsNotNone(file_doc_name)

        # Load file
        file_doc = frappe.get_doc("File", file_doc_name)

        # 3) File must be private
        self.assertEqual(file_doc.is_private, 1)

        # 4) Physical file must exist in the site
        file_path = frappe.get_site_path("private", "files", filename)
        self.assertTrue(os.path.exists(file_path))

        # 5) Content must match original buffer
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertEqual(content, "Linea 1\nLinea 2")

        # 6) Child table must include today's file
        rows = [row for row in c.custom_transcriptions if str(row.date) == self.today]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].transcription_file, expected_url)
