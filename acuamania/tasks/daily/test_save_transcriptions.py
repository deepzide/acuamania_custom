import os

import frappe
from frappe.tests.utils import FrappeTestCase

from acuamania.tasks.daily.save_transcriptions import (
	save_transcriptions,
)

# ================================================================
# CONSTANTS
# ================================================================

CONTACT_FIRST_NAME = "Cron Tester"
CONTACT_EMAIL = "cron@test.com"
CONTACT_PHONE = "091234567"
BUFFER_TEXT = "Hola que tal"
DATE_FORMAT = "%Y-%m-%d"


# ================================================================
# TEST SUITE
# ================================================================


class TestSaveTranscriptions(FrappeTestCase):
	def setUp(self):
		"""Create a fresh Contact with transcription buffer."""
		self.contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": CONTACT_FIRST_NAME,
				"email_id": CONTACT_EMAIL,
				"phone_nos": [{"phone": CONTACT_PHONE}],
				"custom_transcription_text": BUFFER_TEXT,
			}
		).insert(ignore_permissions=True)

		# Site private path for output files
		self.site_private_files = os.path.join(frappe.get_site_path(), "private", "files")

		# Ensure folder exists
		os.makedirs(self.site_private_files, exist_ok=True)

	# ------------------------------------------------------------

	def test_cron_exports_and_clears_buffer(self):
		"""Validates the full daily flow: export → file → history → clear."""

		# Execute scheduled job
		save_transcriptions()

		# Reload contact to get updated fields
		self.contact.reload()

		# -----------------------------
		# 1) Verify buffer was cleared
		# -----------------------------
		self.assertEqual(
			self.contact.custom_transcription_text, "", "Transcription buffer must be cleared after export."
		)

		# -----------------------------
		# 2) Verify history entry exists
		# -----------------------------
		history_rows = self.contact.get("custom_transcriptions")
		self.assertTrue(history_rows, "A transcription history row should have been created.")

		row = history_rows[0]
		file_url = row.transcription_file

		self.assertIsNotNone(file_url, "History entry must include the transcription file URL.")

		# -----------------------------
		# 3) Verify File doc was created
		# -----------------------------
		file_doc_name = frappe.db.exists("File", {"file_url": file_url})
		self.assertIsNotNone(file_doc_name, "File DocType must be created for daily transcription export.")

		file_doc = frappe.get_doc("File", file_doc_name)
		self.assertEqual(file_doc.is_private, 1)

		# -----------------------------
		# 4) Verify physical file exists
		# -----------------------------
		physical_path = os.path.join(frappe.get_site_path(), file_url.lstrip("/"))

		self.assertTrue(os.path.exists(physical_path), f"Expected file to exist at: {physical_path}")

		# -----------------------------
		# 5) Verify file content matches buffer
		# -----------------------------
		with open(physical_path, encoding="utf-8") as f:
			content = f.read().strip()

		self.assertEqual(content, BUFFER_TEXT, "File contents must match the original transcription buffer.")
