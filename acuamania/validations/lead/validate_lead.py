import frappe

PHONE_FIELD = "phone"
MSG_NO_PHONE = "El Lead debe tener un número telefónico para crear el contacto."


def validate_lead(doc, method):
	if not getattr(doc, PHONE_FIELD):
		frappe.throw(MSG_NO_PHONE)
