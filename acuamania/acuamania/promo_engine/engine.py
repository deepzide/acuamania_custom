import frappe
from frappe.utils import today
from acuamania.acuamania.promo_engine.rules import (
    apply_required_x_free,
    apply_fixed_price,
    apply_percentage_discount,
    apply_discount_amount,
)

GROUP_PROMO_LABEL = "Descuento de Grupo"
ENTRADA_ITEM_GROUP = "Entrada"
GROUP_PROMO_MIN_QTY_EXCLUSIVE = 15


def apply_selected_promotion(doc, method=None):
    """
    Called on Quotation/Sales Order validate/before_save.
    Supports ANY number of promotions via child table:
        doc.custom_promotion_table

    Auto-injects 'Descuento de Grupo' when total qty of items in 'Entrada'
    item group (including its descendants) is > 15, only if promo is active.
    """

    reset_discount_fields(doc)
    ensure_totals_are_initialized(doc)

    items_by_code = group_items_by_code(doc)
    if not items_by_code:
        return

    ensure_group_promotion_if_applicable(doc)

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


def ensure_totals_are_initialized(doc):
    """
    Ensures grand_total and related fields exist before
    ERPNext payment schedule validation runs.
    """
    try:
        doc.run_method("calculate_taxes_and_totals")
    except Exception:
        pass


def ensure_group_promotion_if_applicable(doc):
    """
    Adds 'Descuento de Grupo' to custom_promotion_table when Entrada qty > 15,
    only if the promotion exists and is active. Idempotent.
    """
    entrada_qty = get_total_qty_for_item_group(doc, ENTRADA_ITEM_GROUP)

    if entrada_qty <= GROUP_PROMO_MIN_QTY_EXCLUSIVE:
        return

    promo_name = get_active_promotion_name_by_label(GROUP_PROMO_LABEL)
    if not promo_name:
        return

    promotion_rows = doc.get("custom_promotion_table") or []
    if promotion_already_present(promotion_rows, promo_name):
        return

    doc.append("custom_promotion_table", {"promotion": promo_name})


def get_total_qty_for_item_group(doc, item_group_name):
    """
    Sums qty for items where Item.item_group is the given item_group_name
    or a descendant of it.
    """
    root_group = frappe.db.get_value(
        "Item Group",
        {"item_group_name": item_group_name},
        "name",
    ) or item_group_name

    group_names = get_item_group_tree_names(root_group)
    if not group_names:
        group_names = [root_group]

    item_codes = get_item_codes_by_item_groups(group_names)
    if not item_codes:
        return 0

    total = 0
    for row in getattr(doc, "items", []) or []:
        if row.item_code in item_codes:
            total += float(row.qty or 0)

    return total


def get_item_group_tree_names(root_group_name):
    """
    Returns root + descendants using nested set (lft/rgt).
    """
    bounds = frappe.db.get_value(
        "Item Group", root_group_name, ["lft", "rgt"], as_dict=True
    )
    if not bounds:
        return []

    return frappe.get_all(
        "Item Group",
        filters={
            "lft": [">=", bounds.lft],
            "rgt": ["<=", bounds.rgt],
        },
        pluck="name",
        order_by="lft asc",
    )


def get_item_codes_by_item_groups(item_group_names):
    """
    Returns item codes for items that belong to any of the given item groups.
    """
    if not item_group_names:
        return set()

    return set(
        frappe.get_all(
            "Item",
            filters={"item_group": ["in", item_group_names]},
            pluck="name",
        )
        or []
    )


def get_active_promotion_name_by_label(promotion_label):
    """
    Finds an active Park Promotion by promotion_name (human label).
    Returns its docname or None.
    """
    return frappe.db.get_value(
        "Park Promotion",
        {"promotion_name": promotion_label, "active": 1},
        "name",
    )


def promotion_already_present(rows, promo_name):
    for row in rows or []:
        if row.promotion == promo_name:
            return True
    return False


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
    if not promo or not getattr(promo, "active", 0):
        row.applied_name = ""
        row.discount = 0
        return

    discount = calculate_discount(promo, items_by_code)
    row.applied_name = promo.promotion_name or promo.name
    row.discount = discount


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
    return dispatch_promotion_logic(promo, items_by_code) or 0


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
