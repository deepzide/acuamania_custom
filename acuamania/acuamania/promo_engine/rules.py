import frappe


def resolve_applicable_item_codes(promo, items_by_code):
    """
    Determina qué item_codes son elegibles para la promoción:
    - Si el Park Promotion tiene filas en la tabla hija items: solo esos item_code.
    - Si no, se aplica a todos los item_code del documento.
    """
    explicit_codes = {
        row.product
        for row in getattr(promo, "park_promotion_items", []) or []
        if getattr(row, "product", None)
    }

    if explicit_codes:
        return [code for code in explicit_codes if code in items_by_code]

    return list(items_by_code.keys())


def apply_two_for_one(promo, items_by_code):
    """
    Lógica 2x1: por cada 2 unidades, 1 es gratis.
    Descuento = free_units * unit_rate.
    """
    applicable_codes = resolve_applicable_item_codes(promo, items_by_code)
    total_discount = 0

    for code in applicable_codes:
        rows = items_by_code.get(code, [])
        if not rows:
            continue

        total_qty = sum(row.qty for row in rows if row.qty)
        if not total_qty:
            continue

        min_qty = promo.min_qty_required or 2
        if total_qty < min_qty:
            continue

        free_units = total_qty // 2
        if not free_units:
            continue

        unit_rate = rows[0].rate or 0
        if not unit_rate:
            continue

        total_discount += free_units * unit_rate

    return total_discount


def apply_three_for_two(promo, items_by_code):
    """
    Lógica 3x2: por cada 3 unidades, 1 es gratis.
    """
    applicable_codes = resolve_applicable_item_codes(promo, items_by_code)
    total_discount = 0

    for code in applicable_codes:
        rows = items_by_code.get(code, [])
        if not rows:
            continue

        total_qty = sum(row.qty for row in rows if row.qty)
        if not total_qty:
            continue

        min_qty = promo.min_qty_required or 3
        if total_qty < min_qty:
            continue

        free_units = total_qty // 3
        if not free_units:
            continue

        unit_rate = rows[0].rate or 0
        if not unit_rate:
            continue

        total_discount += free_units * unit_rate

    return total_discount


def apply_fixed_price(promo, items_by_code):
    """
    Precio fijo por unidad.
    Descuento = max(0, current_rate - fixed_price) * qty
    """
    if not promo.fixed_price:
        return 0

    applicable_codes = resolve_applicable_item_codes(promo, items_by_code)
    total_discount = 0

    for code in applicable_codes:
        rows = items_by_code.get(code, [])
        if not rows:
            continue

        for row in rows:
            if not row.qty:
                continue

            current_rate = row.rate or 0
            if current_rate <= promo.fixed_price:
                continue

            unit_discount = current_rate - promo.fixed_price
            total_discount += unit_discount * row.qty

    return total_discount


def apply_percentage_discount(promo, items_by_code):
    """
    Descuento porcentual sobre el subtotal de los ítems aplicables.
    """
    if not promo.discount_percentage:
        return 0

    applicable_codes = resolve_applicable_item_codes(promo, items_by_code)
    base_amount = 0

    for code in applicable_codes:
        rows = items_by_code.get(code, [])
        for row in rows:
            if not row.qty or not row.rate:
                continue
            base_amount += row.qty * row.rate

    if not base_amount:
        return 0

    return base_amount * (promo.discount_percentage / 100.0)


def apply_discount_amount(promo, items_by_code):
    """
    Descuento fijo a nivel de documento, siempre que haya
    al menos un item elegible.
    """
    if not promo.discount_amount:
        return 0

    applicable_codes = resolve_applicable_item_codes(promo, items_by_code)
    has_items = any(items_by_code.get(code) for code in applicable_codes)
    if not has_items:
        return 0

    return promo.discount_amount
