import frappe

STATUS_CATEGORIES = {"Nuevo", "Recurrente"}
GROUP_CATEGORY = "Grupo"
CORPORATE_CATEGORY = "Corporativo"
HOTEL_CATEGORY = "Hotel"


def classify_lead(doc):
    """Classify Lead as Nuevo/Recurrente/Grupo/Corporativo/Hotel before insert."""
    phone_number = (doc.phone or "").strip()
    if not phone_number:
        return

    contact_name = frappe.db.exists("Contact", {"phone": phone_number})
    base_status = "Recurrente" if contact_name else "Nuevo"

    classifications = {base_status}
    classifications.update(_resolve_additional(doc))
    _apply_to_lead(doc, classifications)


def _resolve_additional(doc):
    """Return additional classifications based on custom fields."""
    results = set()
    if getattr(doc, "custom_qty_person", 1) > 1:
        results.add(GROUP_CATEGORY)
    if getattr(doc, "custom_has_active_convenio", 0):
        results.add(CORPORATE_CATEGORY)
        doc.is_corpo = 1
    if getattr(doc, "custom_has_hotel_voucher", 0):
        results.add(HOTEL_CATEGORY)
    return results


def _apply_to_lead(lead_doc, categories):
    """Assign categories to Lead, ensuring 'Nuevo' and 'Recurrente' exclusivity."""
    for category in categories:
        if category in STATUS_CATEGORIES:
            _set_exclusive_status(lead_doc, category)
        else:
            _append_if_missing(lead_doc, category)


def _set_exclusive_status(document, status):
    """Keep only one of 'Nuevo' or 'Recurrente'."""
    opposite = "Recurrente" if status == "Nuevo" else "Nuevo"
    preserved = [r for r in document.custom_customer_category if r.customer_category != opposite]
    has_status = any(r.customer_category == status for r in preserved)

    document.set("custom_customer_category", [])
    for row in preserved:
        document.append("custom_customer_category", {"customer_category": row.customer_category})

    if not has_status:
        document.append("custom_customer_category", {"customer_category": status})


def _append_if_missing(document, category):
    """Append category if not already present."""
    existing = [r.customer_category for r in document.custom_customer_category]
    if category not in existing:
        document.append("custom_customer_category", {"customer_category": category})
