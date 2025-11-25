import frappe


def resolve_applicable_items(promo, items_by_code):
    """
    Decides which items codes apply:
    - If promotion has child table items → only those
    - Else apply_to_item_group
    - Else fallback: apply to all items in the document
    """
    explicit = {row.item_code for row in promo.items if row.item_code}

    if explicit:
        return [code for code in explicit if code in items_by_code]

    if promo.apply_to_item_group:
        all_codes = items_by_code.keys()
        groups = get_groups_for_items(all_codes)
        return [
            code for code in all_codes
            if groups.get(code) == promo.apply_to_item_group
        ]

    return list(items_by_code.keys())


def get_groups_for_items(item_codes):
    if not item_codes:
        return {}

    rows = frappe.get_all(
        "Item",
        filters={"name": ["in", item_codes]},
        fields=["name", "item_group"]
    )
    return {r.name: r.item_group for r in rows}


# ---------------------
# PROMOTION LOGIC
# ---------------------

def apply_two_for_one(promo, items_by_code):
    """
    Classic 2x1: free_units = qty // 2
    """
    applicable = resolve_applicable_items(promo, items_by_code)
    total_discount = 0

    for code in applicable:
        rows = items_by_code[code]
        qty = sum(r.qty for r in rows)
        if qty < (promo.min_qty_required or 2):
            continue

        free_units = qty // 2
        unit_rate = rows[0].rate

        total_discount += free_units * unit_rate

    return total_discount


def apply_three_for_two(promo, items_by_code):
    applicable = resolve_applicable_items(promo, items_by_code)
    total_discount = 0

    for code in applicable:
        rows = items_by_code[code]
        qty = sum(r.qty for r in rows)
        if qty < (promo.min_qty_required or 3):
            continue

        free_units = qty // 3
        unit_rate = rows[0].rate

        total_discount += free_units * unit_rate

    return total_discount


def apply_fixed_price(promo, items_by_code):
    """
    Discount = (unit_rate - fixed_price) * qty
    """
    if not promo.fixed_price:
        return 0

    applicable = resolve_applicable_items(promo, items_by_code)
    total_discount = 0

    for code in applicable:
        rows = items_by_code[code]
        for row in rows:
            if row.rate > promo.fixed_price:
                total_discount += (row.rate - promo.fixed_price) * row.qty

    return total_discount


def apply_percentage_discount(promo, items_by_code):
    if not promo.discount_percentage:
        return 0

    applicable = resolve_applicable_items(promo, items_by_code)
    base = 0

    for code in applicable:
        rows = items_by_code[code]
        for row in rows:
            base += row.qty * row.rate

    return base * (promo.discount_percentage / 100)


def apply_discount_amount(promo, items_by_code):
    """
    Flat discount_amount applied only if items match.
    """
    if not promo.discount_amount:
        return 0

    applicable = resolve_applicable_items(promo, items_by_code)
    if not applicable:
        return 0

    return promo.discount_amount
