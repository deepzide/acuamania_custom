import frappe
from frappe.utils import cstr


def normalize_contact_phone(doc, method=None):
	"""Synchronize Contact.phone and custom_phone in both directions, preferring custom_phone when present."""
	if frappe.flags.in_patch or frappe.flags.in_migrate:
		return

	if not hasattr(doc, "custom_phone"):
		return

	phone = cstr(doc.phone).strip()
	custom_phone = cstr(doc.custom_phone).strip()

	if custom_phone:
		if phone != custom_phone:
			doc.phone = custom_phone
			frappe.logger("contact_phone_sync").info(
				f"Set Contact.phone from custom_phone for {doc.name}: {custom_phone}"
			)

	elif phone:
		doc.custom_phone = phone
		frappe.logger("contact_phone_sync").info(
			f"Set Contact.custom_phone from phone for {doc.name}: {phone}"
		)
