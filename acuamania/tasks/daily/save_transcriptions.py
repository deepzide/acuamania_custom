import os

import frappe


def save_transcriptions():
	"""
	Daily scheduled job.

	Iterates over all Contacts with buffered transcriptions and
	exports them into private File records, appending history and
	clearing the buffer.
	"""
	today = frappe.utils.nowdate()

	contact_names = frappe.get_all(
		"Contact",
		filters=[["custom_transcription_text", "!=", ""]],
		pluck="name",
	)

	for contact_name in contact_names:
		contact = frappe.get_doc("Contact", contact_name)
		process_contact_transcription(contact, today)

	frappe.db.commit()


def process_contact_transcription(contact, date):
	"""
	Process a single Contact transcription buffer.
	Returns True if processed, False if skipped.
	"""
	raw_text = contact.custom_transcription_text
	cleaned = sanitize(raw_text)

	if not cleaned:
		return False

	file_doc = create_private_file(contact.name, date, cleaned)
	append_history(contact, file_doc, date)
	clear_buffer(contact)

	return True


def sanitize(text: str) -> str:
	if not text:
		return ""
	return str(text).replace("\r", " ").strip()


def create_private_file(contact_name: str, date: str, content: str):
	"""
	Creates a private File:
	/private/files/TRS-<contact>-<date>.txt
	"""

	private_files_path = os.path.join(
		frappe.get_site_path(), "private", "files"
	)
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
	Appends a history row if not already present for the given date.
	"""
	for row in contact.get("custom_transcriptions") or []:
		if str(row.date) == str(date):
			return

	contact.append(
		"custom_transcriptions",
		{
			"date": date,
			"transcription_file": file_doc.file_url,
		},
	)


def clear_buffer(contact):
	contact.custom_transcription_text = ""
	contact.save(ignore_permissions=True)
