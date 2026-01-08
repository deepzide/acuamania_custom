import frappe
from frappe.utils import cstr


frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("set_mobile_no", file_count=50)

def normalize_contact_phone(doc, method=None):
	"""Synchronize Contact.phone and custom_phone in both directions, preferring custom_phone when present."""
	if frappe.flags.in_patch or frappe.flags.in_migrate:
		return

	if not hasattr(doc, "custom_phone"):
		return

	if doc.custom_phone:
		custom_phone = cstr(doc.custom_phone).strip()
		if doc.phone != custom_phone:
			doc.phone = custom_phone
			frappe.logger("contact_phone_sync").info(
				f"Set Contact.phone from custom_phone for {doc.name}: {custom_phone}"
			)

	elif doc.phone:
		phone = cstr(doc.phone).strip()
		doc.custom_phone = phone
		frappe.logger("contact_phone_sync").info(
			f"Set Contact.custom_phone from phone for {doc.name}: {phone}"
		)

	doc.mobile_no = doc.phone or doc.custom_phone
	logger.debug(f"Normalized phone numbers for Contact {doc.name}: phone={doc.phone}, custom_phone={doc.custom_phone}, mobile_no={doc.mobile_no}")