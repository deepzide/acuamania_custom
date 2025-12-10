import frappe

STATUS_CATEGORIES = {"Nuevo", "Recurrente"}
RESIDENT_CATEGORY = "Residente"
GROUP_CATEGORY = "Grupo"
CORPORATE_CATEGORY = "Corporativo"
HOTEL_CATEGORY = "Hotel"


# ============================================
# PUBLIC API — pequeños clasificadores atómicos
# ============================================

def classify_base_status(doc):
    """
    Clasifica como Nuevo/Recurrente.
    Atomizado para ejecutarse desde cualquier hook.
    """
    phone_number = (doc.phone or "").strip()
    if not phone_number:
        return

    contact_exists = frappe.db.exists("Contact", {"phone": phone_number})
    status = "Recurrente" if contact_exists else "Nuevo"

    _apply_to_lead(doc, {status})


def classify_group(doc):
    """
    Detecta si el lead es 'Grupo'.
    """
    if getattr(doc, "custom_person_qty", 1) > 1:
        _apply_to_lead(doc, {GROUP_CATEGORY})


def classify_corporate(doc):
    """
    Detecta si es 'Corporativo'.
    """
    if getattr(doc, "is_corpo", 0):
        _apply_to_lead(doc, {CORPORATE_CATEGORY})


def classify_hotel(doc):
    """
    Detecta si es 'Hotel'.
    """
    if getattr(doc, "custom_has_hotel_voucher", 0):
        _apply_to_lead(doc, {HOTEL_CATEGORY})


def classify_resident(doc):
    """
    Detecta si es 'Residente' según el territorio.
    """
    if _is_resident_territory(doc):
        _apply_to_lead(doc, {RESIDENT_CATEGORY})


# ============================================
# ORQUESTADOR OPCIONAL (antes era classify_lead)
# ============================================

def classify_lead(doc):
    """
    Orquestador opcional, puedes eliminarlo y ejecutar cada clasificador
    desde distintos hooks si quieres.
    """
    classify_base_status(doc)
    classify_group(doc)
    classify_corporate(doc)
    classify_hotel(doc)
    classify_resident(doc)


# ============================================
# HELPERS INTERNOS — lógica común
# ============================================

def _is_resident_territory(doc):
    territory = getattr(doc, "territory", None)
    if not territory:
        return False

    is_resident = frappe.db.get_value("Territory", territory, "custom_is_resident")
    return bool(is_resident)


def _apply_to_lead(lead_doc, categories):
    for category in categories:
        if category in STATUS_CATEGORIES:
            _set_exclusive_status(lead_doc, category)
        else:
            _append_if_missing(lead_doc, category)


def _set_exclusive_status(document, status):
    opposite = "Recurrente" if status == "Nuevo" else "Nuevo"

    preserved = [
        r for r in document.custom_customer_category
        if r.customer_category != opposite
    ]

    document.set("custom_customer_category", preserved)

    if not any(r.customer_category == status for r in preserved):
        document.append("custom_customer_category", {"customer_category": status})


def _append_if_missing(document, category):
    existing = [r.customer_category for r in document.custom_customer_category]
    if category not in existing:
        document.append("custom_customer_category", {"customer_category": category})
