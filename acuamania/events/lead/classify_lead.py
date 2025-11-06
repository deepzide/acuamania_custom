import frappe

STATUS_CATEGORIES = {"Nuevo", "Recurrente"}
GROUP_CATEGORY = "Grupo"
CORPORATE_CATEGORY = "Corporativo"
HOTEL_CATEGORY = "Hotel"


def classify_lead(doc, method=None):
    """Classify Lead as Nuevo/Recurrente/Grupo/Corporativo/Hotel before insert and propagate to related records."""
    phone_number = (doc.phone or "").strip()
    if not phone_number:
        return

    contact_name = _get_contact_by_phone(phone_number)
    base_status = _resolve_base_status_category(contact_name)

    classifications = {base_status}
    classifications.update(_resolve_additional_classifications(doc))

    _apply_classifications_to_lead(doc, classifications)

    if contact_name:
        _propagate_classifications_to_related_records(contact_name, classifications)


def _get_contact_by_phone(phone_number):
    """Return the name of an existing Contact for a given phone number."""
    return frappe.db.exists("Contact", {"phone": phone_number})


def _resolve_base_status_category(contact_name):
    """Return 'Recurrente' if the contact exists, otherwise 'Nuevo'."""
    return "Recurrente" if contact_name else "Nuevo"


def _resolve_additional_classifications(doc):
    """Return a set of additional classifications based on custom fields."""
    classifications = set()

    if getattr(doc, "custom_qty_person", 1) > 1:
        classifications.add(GROUP_CATEGORY)

    if getattr(doc, "custom_has_active_convenio", 0):
        classifications.add(CORPORATE_CATEGORY)
        doc.is_corpo = 1

    if getattr(doc, "custom_has_hotel_voucher", 0):
        classifications.add(HOTEL_CATEGORY)

    return classifications


def _apply_classifications_to_lead(lead_doc, classifications):
    """Apply all status and classification categories to the Lead before insert."""
    for category in classifications:
        _set_status_category_for_document(lead_doc, category)


def _propagate_classifications_to_related_records(contact_name, classifications):
    """Propagate classifications to Contact and Customer if they exist."""
    contact_doc = frappe.get_doc("Contact", contact_name)
    for category in classifications:
        _set_status_category_for_document(contact_doc, category)

    customer_doc = _get_customer_linked_to_contact(contact_doc)
    if not customer_doc:
        return

    for category in classifications:
        _set_status_category_for_document(customer_doc, category)


def _get_customer_linked_to_contact(contact_doc):
    """Return the Customer linked to this Contact via customer_primary_contact."""
    customer_name = frappe.db.get_value("Customer", {"customer_primary_contact": contact_doc.name})
    return frappe.get_doc("Customer", customer_name) if customer_name else None


def _set_status_category_for_document(document, category):
    """Ensure the document has the given classification and keeps consistency."""
    if not hasattr(document, "custom_customer_category"):
        return

    _set_status_category(document, category)

    if document.doctype == "Lead":
        return

    document.save(ignore_permissions=True)


def _set_status_category(document, category):
    """Append the given category if not already present and remove conflicting status where needed."""
    if category in STATUS_CATEGORIES:
        _normalize_status_categories(document, category)
        return

    existing = [row.customer_category for row in document.custom_customer_category]
    if category not in existing:
        document.append("custom_customer_category", {"customer_category": category})


def _normalize_status_categories(document, new_status):
    """Keep either 'Nuevo' or 'Recurrente', not both."""
    opposite = "Recurrente" if new_status == "Nuevo" else "Nuevo"

    preserved_rows = [
        row for row in document.custom_customer_category if row.customer_category != opposite
    ]

    already_has = any(row.customer_category == new_status for row in preserved_rows)

    document.set("custom_customer_category", [])
    for row in preserved_rows:
        document.append("custom_customer_category", {"customer_category": row.customer_category})

    if not already_has:
        document.append("custom_customer_category", {"customer_category": new_status})
