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


def upsert_contact(doc, method):
    if not getattr(doc, PHONE_FIELD):
        frappe.throw(MSG_NO_PHONE)
        return
    contact = get_or_create_contact_from_lead(doc)
    link_contact_to_lead(doc, contact)


def get_or_create_contact_from_lead(doc):
    phone_number = getattr(doc, PHONE_FIELD).strip()
    existing_contact_name = frappe.db.exists(CONTACT_DOCTYPE, {PHONE_FIELD: phone_number})

    if not existing_contact_name:
        contact_phone = frappe.db.get_value("Contact Phone", {"phone": phone_number}, "parent")
        if contact_phone:
            existing_contact_name = contact_phone

    if existing_contact_name:
        frappe.msgprint(MSG_EXISTING_CONTACT.format(name=existing_contact_name))
        return frappe.get_doc(CONTACT_DOCTYPE, existing_contact_name)
    
    contact = build_contact_from_lead(doc, phone_number)
    contact.insert(ignore_permissions=True)
    contact.reload()
    frappe.msgprint(MSG_NEW_CONTACT.format(name=contact.name))
    return contact


def build_contact_from_lead(doc, phone_number):
    contact = frappe.new_doc(CONTACT_DOCTYPE)
    contact.first_name = getattr(doc, "first_name", "") or getattr(doc, "lead_name", "")
    contact.last_name = getattr(doc, "last_name", "")
    contact.salutation = getattr(doc, "salutation", "")
    contact.gender = getattr(doc, "gender", "")
    contact.designation = getattr(doc, "job_title", "")
    contact.company_name = getattr(doc, "company_name", "")
    contact.phone = phone_number
    contact.custom_territory = getattr(doc, "territory", "")
    mobile_value = getattr(doc, MOBILE_FIELD, "")

    if mobile_value:
        contact.mobile_no = mobile_value
    email_value = getattr(doc, EMAIL_FIELD, "")
    if email_value:
        contact.append(EMAIL_CHILD_TABLE, {"email_id": email_value, "is_primary": 1})

    contact.append(PHONE_CHILD_TABLE, {"phone": phone_number, "is_primary_phone": 1})
    return contact


def link_contact_to_lead(doc, contact):
    current_contact = getattr(doc, CUSTOM_CONTACT_LINK_FIELD, None)
    if current_contact == contact.name:
        return
    setattr(doc, CUSTOM_CONTACT_LINK_FIELD, contact.name)
    doc.save(ignore_permissions=True)
