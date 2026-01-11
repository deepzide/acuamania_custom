import os

import frappe
from frappe.tests.utils import FrappeTestCase

from acuamania.tasks.daily.save_transcriptions import save_transcriptions


CONTACT_FIRST_NAME = "Cron Tester"
CONTACT_PHONE = "091234567"
BUFFER_TEXT = "Hola que tal"


class TestSaveTranscriptions(FrappeTestCase):
	def setUp(self):
		self.contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": CONTACT_FIRST_NAME,
				"phone_nos": [{"phone": CONTACT_PHONE}],
				"custom_transcription_text": BUFFER_TEXT,
			}
		).insert(ignore_permissions=True)

		self.private_files_path = os.path.join(
			frappe.get_site_path(), "private", "files"
		)
		os.makedirs(self.private_files_path, exist_ok=True)

	# ------------------------------------------------------------

	def test_single_contact_export_and_clear(self):
		save_transcriptions()
		self.contact.reload()

		self.assertEqual(self.contact.custom_transcription_text, "")

		history = self.contact.get("custom_transcriptions")
		self.assertEqual(len(history), 1)

		file_url = history[0].transcription_file
		file_name = frappe.db.exists("File", {"file_url": file_url})
		self.assertIsNotNone(file_name)

		physical_path = os.path.join(
			frappe.get_site_path(), file_url.lstrip("/")
		)
		self.assertTrue(os.path.exists(physical_path))

		with open(physical_path, encoding="utf-8") as f:
			content = f.read().strip()

		self.assertEqual(content, BUFFER_TEXT)

	# ------------------------------------------------------------

	def test_multiple_contacts_are_processed(self):
		second = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "Second",
				"custom_transcription_text": "Segundo texto",
			}
		).insert(ignore_permissions=True)

		save_transcriptions()

		self.contact.reload()
		second.reload()

		self.assertEqual(self.contact.custom_transcription_text, "")
		self.assertEqual(second.custom_transcription_text, "")

		self.assertEqual(len(self.contact.custom_transcriptions), 1)
		self.assertEqual(len(second.custom_transcriptions), 1)

	# ------------------------------------------------------------

	def test_empty_contact_is_ignored(self):
		empty = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "Empty",
				"custom_transcription_text": "",
			}
		).insert(ignore_permissions=True)

		save_transcriptions()
		empty.reload()

		self.assertFalse(empty.get("custom_transcriptions"))

	# ------------------------------------------------------------

	def test_cron_is_idempotent(self):
		save_transcriptions()
		save_transcriptions()

		self.contact.reload()

		self.assertEqual(
			len(self.contact.custom_transcriptions),
			1,
		)
