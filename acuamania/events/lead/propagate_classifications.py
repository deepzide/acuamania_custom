import frappe


def propagate_classifications(doc):
    """Propagate Lead classifications to Contact and Customer after insert by copying categories as-is."""
    phone_number = (doc.phone or "").strip()
    if not phone_number:
        return

    contact_name = frappe.db.get_value("Contact", {"phone": phone_number}, "name")
    if not contact_name:
        return

    contact_doc = frappe.get_doc("Contact", contact_name)
    customer_doc = _get_customer_by_contact(contact_doc)

    lead_categories = _collect_lead_classifications(doc)
    if not lead_categories:
        return

    _copy_categories(contact_doc, lead_categories)
    if customer_doc:
        _copy_categories(customer_doc, lead_categories)


def _collect_lead_classifications(lead_doc):
    """Return the list of classifications stored on the Lead."""
    if not getattr(lead_doc, "custom_customer_category", None):
        return []
    return [row.customer_category for row in lead_doc.custom_customer_category]


def _get_customer_by_contact(contact_doc):
    """Return the Customer linked to this Contact."""
    name = frappe.db.get_value("Customer", {"customer_primary_contact": contact_doc.name})
    return frappe.get_doc("Customer", name) if name else None


def _copy_categories(target_doc, categories):
    """Replace the target document's categories with those from the Lead."""
    if not hasattr(target_doc, "custom_customer_category"):
        return

    target_doc.set("custom_customer_category", [])
    for category in categories:
        target_doc.append("custom_customer_category", {"customer_category": category})

    target_doc.save(ignore_permissions=True)
