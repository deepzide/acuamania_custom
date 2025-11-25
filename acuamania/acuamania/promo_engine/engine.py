import frappe
from frappe.utils import today
from acuamania.acuamania.promo_engine.rules import (
    apply_two_for_one,
    apply_three_for_two,
    apply_fixed_price,
    apply_percentage_discount,
    apply_discount_amount
)


def apply_promotions(doc, method):
    """
    Main entry point for Quotation and Sales Order.
    Evaluates active promotions and applies ONE (non-stackable).
    """
    if not doc.items:
        return

    if has_manual_discount(doc):
        return

    promo_list = fetch_active_promotions(doc)
    if not promo_list:
        return

    items_by_code = group_items(doc)

    for promo in promo_list:
        if not is_promo_valid_for_doc(doc, promo):
            continue

        discount = dispatch_promo_logic(doc, promo, items_by_code)
        if discount and discount > 0:
            apply_document_discount(doc, discount)
            annotate_promotion(doc, promo)
            break


def has_manual_discount(doc):
    amt = getattr(doc, "additional_discount_amount", 0) or 0
    pct = getattr(doc, "additional_discount_percentage", 0) or 0
    return amt > 0 or pct > 0


def fetch_active_promotions(doc):
    """
    Returns all Park Promotion matching today's date.
    """
    doc_date = (
        getattr(doc, "transaction_date", None)
        or getattr(doc, "posting_date", None)
        or today()
    )

    promos = frappe.get_all(
        "Park Promotion",
        filters={
            "active": 1,
            "valid_from": ["<=", doc_date],
            "valid_upto": [">=", doc_date]
        },
        fields=["name"]
    )

    return [frappe.get_doc("Park Promotion", p.name) for p in promos]


def group_items(doc):
    """
    Build dict like:
    {
        "ENTR-GRAL": [row1, row2],
        "ENTR-NINO": [row3]
    }
    """
    grouped = {}
    for it in doc.items:
        if not it.item_code:
            continue
        grouped.setdefault(it.item_code, []).append(it)
    return grouped


def is_promo_valid_for_doc(doc, promo):
    """
    Check customer group exclusions (for future extension).
    """
    customer = getattr(doc, "customer", None)
    if not customer:
        return True

    excluded = getattr(promo, "excluded_customer_groups", None)
    if not excluded:
        return True

    customer_group = frappe.db.get_value("Customer", customer, "customer_group")
    if not customer_group:
        return True

    excluded_list = [
        x.strip().lower()
        for x in excluded.split(",")
        if x.strip()
    ]

    return customer_group.lower() not in excluded_list


def dispatch_promo_logic(doc, promo, items):
    """
    Calls the correct rule implementation based on apply_type.
    """
    t = promo.apply_type

    if t == "2x1":
        return apply_two_for_one(promo, items)

    if t == "3x2":
        return apply_three_for_two(promo, items)

    if t == "fixed_price":
        return apply_fixed_price(promo, items)

    if t == "percentage":
        return apply_percentage_discount(promo, items)

    if t == "discount_amount":
        return apply_discount_amount(promo, items)

    return 0


def apply_document_discount(doc, discount_amount):
    """
    Applies a flat discount to Grand Total.
    """
    doc.apply_discount_on = "Grand Total"
    doc.additional_discount_percentage = 0
    doc.additional_discount_amount = discount_amount


def annotate_promotion(doc, promo):
    """
    Optional: store the promo that was applied.
    Requires custom field custom_promotion_name.
    """
    if hasattr(doc, "custom_promotion_name"):
        doc.custom_promotion_name = promo.promotion_name or promo.name
