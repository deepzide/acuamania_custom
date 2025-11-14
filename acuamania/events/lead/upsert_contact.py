import frappe
import logging
import sys
import os

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
    """Return a logger that writes to both stdout and a log file, visible in tests and runtime."""
    logger_name = "lead_contact_sync"
    logger = logging.getLogger(logger_name)

    if not logger.handlers:
        # Ensure log directory exists
        site_name = frappe.local.site or frappe.get_site_path().split(os.sep)[-2]
        log_dir = frappe.get_site_path("logs")
        os.makedirs(log_dir, exist_ok=True)

        log_path = os.path.join(log_dir, f"{logger_name}.log")

        # --- Console handler (visible in bench run-tests output) ---
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_format = logging.Formatter("[%(levelname)s] %(message)s")
        console_handler.setFormatter(console_format)

        # --- File handler (persistent file logs) ---
        file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        file_handler.setFormatter(file_format)

        # --- Attach both handlers ---
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        logger.propagate = False
        logger.setLevel(logging.DEBUG)

        logger.info("🧩 Logger initialized for lead_contact_sync")
        logger.info(f"📂 Log file: {log_path}")

    return logger


def upsert_contact(doc, method):
    """Create or link a Contact from a Lead record."""
    logger = get_logger()
    phone = getattr(doc, PHONE_FIELD, "").strip()
    lead_name = getattr(doc, "name", "UNKNOWN")

    logger.info(f"📞 upsert_contact triggered for Lead '{lead_name}' with phone '{phone}'")

    if not phone:
        logger.warning(f"❌ Lead '{lead_name}' missing phone number — cannot create Contact")
        frappe.throw(MSG_NO_PHONE)

    contact = get_or_create_contact_from_lead(doc)
    link_contact_to_lead(doc, contact)

    logger.info(f"✅ Lead '{lead_name}' linked to Contact '{contact.name}'")


def get_or_create_contact_from_lead(doc):
    """Retrieve existing Contact or create a new one based on Lead info."""
    logger = get_logger()
    phone_number = getattr(doc, PHONE_FIELD, "").strip()
    lead_name = getattr(doc, "name", "UNKNOWN")

    logger.info(f"🔍 Searching Contact for Lead '{lead_name}' (phone={phone_number})")

    # --- Direct match by Contact.phone ---
    existing_contact_name = frappe.db.exists(CONTACT_DOCTYPE, {PHONE_FIELD: phone_number})
    logger.debug(f"Direct match by Contact.phone: {existing_contact_name}")

    # --- Additional lookup in Contact.mobile_no if not found ---
    if not existing_contact_name:
        existing_contact_name = frappe.db.exists(CONTACT_DOCTYPE, {MOBILE_FIELD: phone_number})
        logger.debug(f"Secondary match by Contact.mobile_no: {existing_contact_name}")

    # --- Guard for invalid or deleted contact names ---
    if existing_contact_name and not frappe.db.exists(CONTACT_DOCTYPE, existing_contact_name):
        logger.warning(f"⚠️ Stale reference found: Contact '{existing_contact_name}' no longer exists.")
        existing_contact_name = None

    if existing_contact_name:
        logger.info(f"Reusing existing Contact '{existing_contact_name}' for Lead '{lead_name}'")
        logger.debug(MSG_EXISTING_CONTACT.format(name=existing_contact_name))
        return frappe.get_doc(CONTACT_DOCTYPE, existing_contact_name)

    # --- Otherwise, create a new Contact ---
    contact = build_contact_from_lead(doc, phone_number)
    contact.insert(ignore_permissions=True)
    contact.reload()

    logger.info(f"🆕 Created new Contact '{contact.name}' from Lead '{lead_name}'")
    logger.debug(MSG_NEW_CONTACT.format(name=contact.name))
    return contact


def build_contact_from_lead(doc, phone_number):
    """Prepare a new Contact document from Lead data."""
    logger = get_logger()
    lead_name = getattr(doc, "name", "UNKNOWN")

    contact = frappe.new_doc(CONTACT_DOCTYPE)
    contact.first_name = getattr(doc, "first_name", "") or getattr(doc, "lead_name", "")
    contact.last_name = getattr(doc, "last_name", "")
    contact.salutation = getattr(doc, "salutation", "")
    contact.gender = getattr(doc, "gender", "")
    contact.designation = getattr(doc, "job_title", "")
    contact.company_name = getattr(doc, "company_name", "")
    contact.phone = phone_number
    contact.custom_territory = getattr(doc, "territory", "")

    logger.debug(
        f"⚙️ Building Contact for Lead '{lead_name}': "
        f"{contact.first_name} {contact.last_name} ({phone_number})"
    )
    contact.append(PHONE_CHILD_TABLE, {"phone": phone_number, "is_primary_phone": 1})
    
    logger.debug(f"Contact data → {contact.as_dict()}")
    return contact


def link_contact_to_lead(doc, contact):
    """Link the Contact back to the Lead via the custom field."""
    logger = get_logger()
    current_contact = getattr(doc, CUSTOM_CONTACT_LINK_FIELD, None)
    lead_name = getattr(doc, "name", "UNKNOWN")

    logger.info(f"🔗 Linking Lead '{lead_name}' to Contact '{contact.name}' (current={current_contact})")

    if current_contact == contact.name:
        logger.debug(f"Link already exists for Lead '{lead_name}', skipping.")
        return

    setattr(doc, CUSTOM_CONTACT_LINK_FIELD, contact.name)
    doc.save(ignore_permissions=True)

    logger.info(f"✅ Contact '{contact.name}' linked successfully to Lead '{lead_name}'")
