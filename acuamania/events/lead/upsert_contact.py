import logging
import os
import sys

import frappe

LEAD_DOCTYPE = "Lead"
CONTACT_DOCTYPE = "Contact"

CUSTOM_CONTACT_LINK_FIELD = "custom_contact_name"
PHONE_FIELD = "phone"
MOBILE_FIELD = "mobile_no"
EMAIL_FIELD = "email_id"
PHONE_CHILD_TABLE = "phone_nos"
EMAIL_CHILD_TABLE = "email_ids"
CUSTOM_TERRITORY_FIELD = "custom_territory"

MSG_NO_PHONE = "El Lead debe tener un número de teléfono para crear un Contacto."
MSG_EXISTING_CONTACT = "El contacto existente '{name}' fue vinculado al Lead."
MSG_NEW_CONTACT = "Contacto {name} creado automáticamente y vinculado al Lead."


def get_logger():
	logger_name = "lead_contact_sync"
	logger = logging.getLogger(logger_name)

	if not logger.handlers:
		log_dir = frappe.get_site_path("logs")
		os.makedirs(log_dir, exist_ok=True)

		log_path = os.path.join(log_dir, f"{logger_name}.log")

		console_handler = logging.StreamHandler(sys.stdout)
		console_handler.setLevel(logging.DEBUG)
		console_format = logging.Formatter("[%(levelname)s] %(message)s")
		console_handler.setFormatter(console_format)

		file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
		file_handler.setLevel(logging.DEBUG)
		file_format = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
		file_handler.setFormatter(file_format)

		logger.addHandler(console_handler)
		logger.addHandler(file_handler)
		logger.propagate = False
		logger.setLevel(logging.DEBUG)

		logger.info("🧩 Logger initialized for lead_contact_sync")
		logger.info(f"📂 Log file: {log_path}")

	return logger


def upsert_contact(doc, method):
	"""
	MAIN entry: Validate, retrieve or create Contact, then link to Lead.
	Atomic, predictable, and side-effect safe.
	"""
	logger = get_logger()
	phone = _extract_phone(doc)
	lead_name = doc.name

	logger.info(f"📞 upsert_contact triggered for Lead '{lead_name}' with phone '{phone}'")

	_validate_lead_has_phone(doc)

	contact = _get_existing_contact(phone) or _create_new_contact(doc, phone)
	_link_contact_to_lead(doc, contact)

	logger.info(f"✅ Lead '{lead_name}' linked to Contact '{contact.name}'")


def _validate_lead_has_phone(doc):
	phone = getattr(doc, PHONE_FIELD, "").strip()
	if not phone:
		raise frappe.ValidationError(MSG_NO_PHONE)


def _get_existing_contact(phone):
	"""
	Returns an existing Contact doc OR None.
	Does NOT create or modify anything.
	"""
	logger = get_logger()

	if not phone:
		return None

	logger.info(f"🔍 Searching Contact for phone '{phone}'")

	contact_name = frappe.db.exists(CONTACT_DOCTYPE, {PHONE_FIELD: phone})

	if not contact_name:
		contact_name = frappe.db.exists(CONTACT_DOCTYPE, {MOBILE_FIELD: phone})

	if contact_name:
		logger.info(MSG_EXISTING_CONTACT.format(name=contact_name))
		return frappe.get_doc(CONTACT_DOCTYPE, contact_name)

	return None


def _create_new_contact(doc, phone):
	"""
	Builds and inserts a new Contact based on Lead info.
	Clean, focused, no lookups here.
	"""
	logger = get_logger()
	lead_name = doc.name

	contact = frappe.new_doc(CONTACT_DOCTYPE)
	contact.first_name = getattr(doc, "first_name", "") or getattr(doc, "lead_name", "")
	contact.last_name = getattr(doc, "last_name", "")
	contact.salutation = getattr(doc, "salutation", "")
	contact.gender = getattr(doc, "gender", "")
	contact.designation = getattr(doc, "job_title", "")
	contact.company_name = getattr(doc, "company_name", "")
	contact.phone = phone
	contact.custom_territory = getattr(doc, "territory", "")
	contact.custom_person_qty = getattr(doc, "custom_person_qty", 1)

	contact.append(PHONE_CHILD_TABLE, {"phone": phone, "is_primary_phone": 1})

	logger.info(
		f"🆕 Creating Contact from Lead '{lead_name}' → {contact.first_name} {contact.last_name} ({phone})"
	)
	previous_skip = getattr(frappe.flags, "skip_contact_to_lead_sync", False)
	frappe.flags.skip_contact_to_lead_sync = True
	try:
		contact.insert(ignore_permissions=True)
		contact.reload()
	finally:
		frappe.flags.skip_contact_to_lead_sync = previous_skip

	logger.info(MSG_NEW_CONTACT.format(name=contact.name))
	return contact


def _link_contact_to_lead(doc, contact):
	"""
	Ensures bidirectional linking safely and atomically.
	Updates the database directly to avoid triggering validations or hooks.
	"""
	logger = get_logger()
	lead_name = doc.name
	current = getattr(doc, CUSTOM_CONTACT_LINK_FIELD, None)

	logger.info(f"🔗 Linking Lead '{lead_name}' to Contact '{contact.name}' (current={current})")

	if current == contact.name:
		logger.debug("Link already exists, skipping.")
		return

	doc.db_set(
		CUSTOM_CONTACT_LINK_FIELD,
		contact.name,
		update_modified=False,
	)

	logger.info(f"✅ Contact '{contact.name}' linked to Lead '{lead_name}'")


def _extract_phone(doc):
	"""
	Extract lead phone consistently.
	Centralizing this avoids duplicated stripping logic.
	"""
	phone = getattr(doc, PHONE_FIELD, "")
	return phone.strip() if phone else ""
