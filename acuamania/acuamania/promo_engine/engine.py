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
    Called on Quotation/Sales Order validate.
    Supports ANY number of promotions via child table:
        doc.custom_promotion_table

    Each row contributes its own discount, and the TOTAL is applied
    to the document.
    """

    reset_discount_fields(doc)

    items_by_code = group_items_by_code(doc)
    if not items_by_code:
        return

    promotion_rows = get_promotion_rows(doc)
    if not promotion_rows:
        return

    total_discount = 0

    for row in promotion_rows:
        process_single_promotion_row(row, items_by_code)
        total_discount += row.discount or 0

    if total_discount <= 0:
        return

    apply_document_discount(doc, total_discount)


def get_promotion_rows(doc):
    """Returns promotion rows or empty list."""
    return doc.get("custom_promotion_table") or []


def process_single_promotion_row(row, items_by_code):
    """
    Processes one promotion row:
        - Loads Park Promotion
        - Calculates discount
        - Saves applied name + discount into the row
    """

    promo = load_promo(row.promotion)
    if not promo:
        row.applied_name = ""
        row.discount = 0
        return

    discount = calculate_discount(promo, items_by_code)

    row.applied_name = promo.promotion_name or promo.name
    row.discount = discount


def safe_get(doc, fieldname):
    return getattr(doc, fieldname, None)


def load_promo(promo_name):
    if not promo_name:
        return None
    try:
        return frappe.get_doc("Park Promotion", promo_name)
    except frappe.DoesNotExistError:
        return None


def calculate_discount(promo, items_by_code):
    if not promo:
        return 0
    discount = dispatch_promotion_logic(promo, items_by_code)
    return discount or 0


def reset_discount_fields(doc):
    doc.apply_discount_on = "Grand Total"
    doc.additional_discount_percentage = 0
    doc.discount_amount = 0


def group_items_by_code(doc):
    grouped = {}
    for row in getattr(doc, "items", []):
        if row.item_code:
            grouped.setdefault(row.item_code, []).append(row)
    return grouped


def dispatch_promotion_logic(promo, items_by_code):
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
