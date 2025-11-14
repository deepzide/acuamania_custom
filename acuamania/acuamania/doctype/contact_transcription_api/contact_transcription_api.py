# Copyright (c) 2025, cegomezpy and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ContactTranscriptionAPI(Document):
	pass


@frappe.whitelist()
def append_transcription(phone: str, message: str):
    """
    Append a text snippet to Contact.custom_transcription_text.
    This buffer will be consolidated daily by a scheduled job.
    """

    validate_input(phone, message)

    contact_name = find_contact_by_phone(phone)
    if not contact_name:
        return ignored_response()

    contact = frappe.get_doc("Contact", contact_name)

    cleaned_message = sanitize_message(message)
    updated_buffer = build_updated_buffer(contact.custom_transcription_text, cleaned_message)

    contact.custom_transcription_text = updated_buffer
    contact.save(ignore_permissions=True)

    return success_response(contact_name, len(updated_buffer))


def validate_input(phone: str, message: str):
    if not phone or not message:
        frappe.throw("Both 'phone' and 'message' are required.")


def find_contact_by_phone(phone: str) -> str | None:
    return frappe.db.get_value("Contact Phone", {"phone": phone.strip()}, "parent")


def sanitize_message(msg: str) -> str:
    return str(msg).replace("\r", " ").strip()


def build_updated_buffer(existing: str, new: str) -> str:
    if existing:
        return f"{existing}\n{new}"
    return new


def ignored_response():
    return {
        "status": "ignored",
        "reason": "Contact not found for this phone"
    }


def success_response(contact_name: str, length: int):
    return {
        "status": "success",
        "contact": contact_name,
        "buffer_length": length
    }
