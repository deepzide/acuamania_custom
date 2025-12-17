import frappe


GROUP_PROMO_NAME = "Descuento de Grupo"


def set_default_group_promo(doc):
    """
    Ensures that the 'Descuento de Grupo' promotion is present
    when custom_person_qty > 15 and the promotion is active.

    - Idempotent
    - Does not override manually selected promotions
    - Skips inactive or missing promotions
    """

    person_qty = getattr(doc, "custom_person_qty", 0) or 0
    if person_qty <= 15:
        return

    promo_name = _get_active_group_promo_name()
    if not promo_name:
        return

    promotion_rows = doc.get("custom_promotion_table") or []

    if _promotion_already_applied(promotion_rows, promo_name):
        return

    doc.append(
        "custom_promotion_table",
        {
            "promotion": promo_name,
        },
    )


def _get_active_group_promo_name():
    """
    Returns the name of the active 'Descuento de Grupo' promotion
    or None if it does not exist or is inactive.
    """
    return frappe.db.get_value(
        "Park Promotion",
        {
            "promotion_name": GROUP_PROMO_NAME,
            "active": 1,
        },
        "name",
    )


def _promotion_already_applied(rows, promo_name):
    for row in rows:
        if row.promotion == promo_name:
            return True
    return False
