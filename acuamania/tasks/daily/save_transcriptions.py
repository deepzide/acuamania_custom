import os

import frappe


def save_transcriptions():
	"""
	Daily scheduled job.

	Consolidates Contact.custom_transcription_text into a PRIVATE File DocType:
	/private/files/TRS-<contact>-<date>.txt

	Then appends that file URL to Contact.custom_transcriptions
	and clears the buffer.
	"""

	today = frappe.utils.nowdate()

	contacts = frappe.get_all(
		"Contact",
		filters=[["custom_transcription_text", "!=", ""]],
		fields=["name", "custom_transcription_text"],
	)

	for row in contacts:
		contact = frappe.get_doc("Contact", row.name)
		raw_text = contact.custom_transcription_text

		cleaned = sanitize(raw_text)
		if not cleaned:
			continue

		file_doc = create_private_file(contact.name, today, cleaned)

		append_history(contact, file_doc, today)

		clear_buffer(contact)

	frappe.db.commit()


def sanitize(text: str) -> str:
	if not text:
		return ""
	return str(text).replace("\r", " ").strip()


def create_private_file(contact_name: str, date: str, content: str):
	"""
	Creates a File DocType stored under:
	/private/files/TRS-<contact>-<date>.txt

	Ensures the /private/files directory exists (important for tests).
	"""

	# --------------------------------------------------------------
	# FIX: Ensure private files directory exists during test runs
	# --------------------------------------------------------------
	private_files_path = os.path.join(frappe.get_site_path(), "private", "files")
	os.makedirs(private_files_path, exist_ok=True)

	filename = f"TRS-{contact_name}-{date}.txt"
	file_url = f"/private/files/{filename}"

	existing = frappe.db.exists("File", {"file_url": file_url})
	if existing:
		frappe.delete_doc("File", existing, ignore_permissions=True)

	file_doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": filename,
			"content": content,
			"is_private": 1,
		}
	)

	file_doc.insert(ignore_permissions=True)

	return file_doc


def append_history(contact, file_doc, date):
	"""
	Append a row to Contact.custom_transcriptions.
	Avoids creating duplicate entries for the same date.
	"""
	for row in contact.get("custom_transcriptions") or []:
		if str(row.date) == str(date):
			return

	contact.append("custom_transcriptions", {"date": date, "transcription_file": file_doc.file_url})


def clear_buffer(contact):
	contact.custom_transcription_text = ""
	contact.save(ignore_permissions=True)
