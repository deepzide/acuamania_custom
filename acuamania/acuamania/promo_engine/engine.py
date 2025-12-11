import frappe
from frappe.utils import today
from acuamania.acuamania.promo_engine.rules import (
    apply_required_x_free,
    apply_fixed_price,
    apply_percentage_discount,
    apply_discount_amount,
)


def apply_selected_promotion(doc, method=None):
    """
    Runs on Quotation/Sales Order validate.
    Calculates:
      • Promo normal → custom_promotion_name
      • Promo combo → custom_combo_promotion_name
    Applies BOTH discounts summed.
    Does NOT modify selection fields.
    """

    reset_discount_fields(doc)

    promo_name = safe_get(doc, "custom_promotion_name")
    combo_promo_name = safe_get(doc, "custom_combo_promotion_name")

    items_by_code = group_items_by_code(doc)
    if not items_by_code:
        return

    promo = load_promo(promo_name)
    combo_promo = load_promo(combo_promo_name)

    discount = calculate_discount(promo, items_by_code)
    combo_discount = calculate_discount(combo_promo, items_by_code)

    total_discount = discount + combo_discount

    if total_discount <= 0:
        return

    apply_document_discount(doc, total_discount)

    annotate_promo_applied(doc, promo)
    annotate_combo_promo_applied(doc, combo_promo)


def safe_get(doc, fieldname):
    """Safely get a field from doc."""
    return getattr(doc, fieldname, None)


def load_promo(promo_name):
    """Safely load Park Promotion doc if exists."""
    if not promo_name:
        return None
    try:
        return frappe.get_doc("Park Promotion", promo_name)
    except frappe.DoesNotExistError:
        return None


def calculate_discount(promo, items_by_code):
    """Return discount for one promotion. If no promo → 0."""
    if not promo:
        return 0
    discount = dispatch_promotion_logic(promo, items_by_code)
    return discount or 0


def reset_discount_fields(doc):
    """
    Reset discount values before recalculating.
    Does NOT clear promo selection fields.
    """
    doc.apply_discount_on = "Grand Total"
    doc.additional_discount_percentage = 0
    doc.discount_amount = 0


def annotate_promo_applied(doc, promo):
    """Write promo normal applied into output field."""
    if not promo:
        return
    if hasattr(doc, "custom_selected_promotion"):
        doc.custom_selected_promotion = promo.promotion_name or promo.name


def annotate_combo_promo_applied(doc, promo):
    """Write combo promo applied into output field."""
    if not promo:
        return
    if hasattr(doc, "custom_combo_selected_promotion"):
        doc.custom_combo_selected_promotion = promo.promotion_name or promo.name


def group_items_by_code(doc):
    """Same as original grouping logic."""
    grouped = {}
    for row in getattr(doc, "items", []):
        if row.item_code:
            grouped.setdefault(row.item_code, []).append(row)
    return grouped


def dispatch_promotion_logic(promo, items_by_code):
    """Same dispatch logic as original."""
    if not promo:
        return 0

    promo_type = promo.apply_type

    if promo_type == "requeridos x gratuitos":
        return apply_required_x_free(promo, items_by_code)

    if promo_type == "precio fijo":
        return apply_fixed_price(promo, items_by_code)

    if promo_type == "porcentaje":
        return apply_percentage_discount(promo, items_by_code)

    if promo_type == "precio de descuento":
        return apply_discount_amount(promo, items_by_code)

    return 0


def get_applicable_promotions(doc):
    """Unchanged."""
    doc_date = (
        getattr(doc, "transaction_date", None)
        or getattr(doc, "posting_date", None)
        or today()
    )

    return frappe.get_all(
        "Park Promotion",
        filters={
            "active": 1,
            "valid_from": ["<=", doc_date],
            "valid_upto": [">=", doc_date],
        },
        fields=["name", "promotion_name", "apply_type"],
        order_by="valid_from asc, promotion_name asc",
    )


def apply_document_discount(doc, discount_amount):
    """Unchanged ERPNext behavior."""
    doc.apply_discount_on = "Grand Total"
    doc.additional_discount_percentage = 0
    doc.discount_amount = discount_amount

    try:
        doc.run_method("apply_discount")
    except Exception:
        pass

    try:
        doc.run_method("calculate_taxes_and_totals")
    except Exception:
        pass
