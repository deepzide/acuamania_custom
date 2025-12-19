import frappe

PHONE_FIELD = "phone"
MSG_NO_PHONE = "Ya existe un contacto con este número telefónico."


def validate_contact(doc, method):
	if getattr(doc, PHONE_FIELD):
		phone_number = getattr(doc, PHONE_FIELD).strip()
		existing_contact_name = frappe.db.exists(
			"Contact", {PHONE_FIELD: phone_number, "name": ["!=", doc.name]}
		)
		if existing_contact_name:
			frappe.throw(MSG_NO_PHONE)
