import frappe


STATUS_CATEGORIES = {"Nuevo", "Recurrente"}


def before_insert(doc, method=None):
    """Handle Lead classification and propagate status categories."""
    phone_number = (doc.phone or "").strip()
    if not phone_number:
        return

    contact_name = _get_contact_by_phone(phone_number)
    status_category = _resolve_status_category(contact_name)

    _set_status_category_to_lead(doc, status_category)
    _propagate_status_to_related_records(contact_name, status_category)


def _get_contact_by_phone(phone_number):
    """Return the name of an existing Contact for a given phone number."""
    return frappe.db.exists("Contact", {"phone": phone_number})


def _resolve_status_category(contact_name):
    """Return 'Recurrente' if the contact exists, otherwise 'Nuevo'."""
    if contact_name:
        return "Recurrente"
    return "Nuevo"


def _set_status_category_to_lead(lead_doc, status_category):
    """Apply the status category to the Lead before insert."""
    _set_status_category_for_document(lead_doc, status_category)


def _propagate_status_to_related_records(contact_name, status_category):
    """Propagate the status category to Contact and Customer records if they exist."""
    if not contact_name:
        return

    contact_doc = frappe.get_doc("Contact", contact_name)
    _set_status_category_for_document(contact_doc, status_category)

    customer_doc = _get_customer_linked_to_contact(contact_doc)
    if not customer_doc:
        return

    _set_status_category_for_document(customer_doc, status_category)


def _get_customer_linked_to_contact(contact_doc):
    """Return the Customer linked to this Contact via customer_primary_contact."""
    customer_name = frappe.db.get_value("Customer", {"customer_primary_contact": contact_doc.name})
    if not customer_name:
        return None
    return frappe.get_doc("Customer", customer_name)


def _set_status_category_for_document(document, status_category):
    """Ensure the document has one valid status category ('Nuevo' or 'Recurrente')."""
    if not hasattr(document, "custom_customer_category"):
        return

    if status_category not in STATUS_CATEGORIES:
        return

    _set_status_category(document, status_category)

    if document.doctype == "Lead":
        return

    document.save(ignore_permissions=True)


def _set_status_category(document, status_category):
    """Keep the given status category, remove the opposite one, preserve other categories."""
    opposite_category = "Recurrente" if status_category == "Nuevo" else "Nuevo"

    preserved_rows = [
        row
        for row in document.custom_customer_category
        if row.customer_category != opposite_category
    ]

    already_has_status = any(
        row.customer_category == status_category for row in preserved_rows
    )

    document.set("custom_customer_category", [])
    for row in preserved_rows:
        document.append("custom_customer_category", {"customer_category": row.customer_category})

    if not already_has_status:
        document.append("custom_customer_category", {"customer_category": status_category})

