import frappe


def resolve_applicable_item_codes(promo, items_by_code):
    """
    Determina qué item_codes son elegibles para la promoción:
    - Si el Park Promotion tiene filas en la tabla hija items: solo esos product.
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


def apply_required_x_free(promo, items_by_code):
    """
    Modelo correcto para tus promociones:
    Por cada 'required' unidades compradas, 'free' de esas mismas unidades son gratis.

    Fórmula:
    groups = total_qty // required
    free_units = groups * free
    discount = free_units * rate
    """

    frappe.msgprint("🔵 DEBUG: Entrando a apply_required_x_free()")

    required = promo.required
    free = promo.free

    frappe.msgprint(f"🔵 DEBUG: required={required}, free={free}")

    if not required or required <= 0:
        frappe.msgprint("🟡 DEBUG: required inválido → 0")
        return 0

    if free is None or free < 0:
        frappe.msgprint("🟡 DEBUG: free inválido → 0")
        return 0

    applicable_codes = resolve_applicable_item_codes(promo, items_by_code)
    frappe.msgprint(f"🔵 DEBUG: applicable_codes={applicable_codes}")

    total_discount = 0

    for code in applicable_codes:
        rows = items_by_code.get(code, [])
        frappe.msgprint(f"🔵 DEBUG: Procesando código '{code}' con {len(rows)} filas")

        total_qty = sum(row.qty for row in rows)
        frappe.msgprint(f"🔵 DEBUG: total_qty={total_qty}")

        if total_qty < required:
            frappe.msgprint("🟡 DEBUG: total_qty < required → no hay grupos")
            continue

        groups = total_qty // required
        free_units = groups * free

        frappe.msgprint(
            f"🔵 DEBUG: groups={groups} (qty {total_qty} // required {required}), "
            f"free_units={free_units}"
        )

        # elegir rate mínimo
        item_rate = min((row.rate or 0) for row in rows)

        item_discount = free_units * item_rate

        frappe.msgprint(
            f"🟣 DEBUG: item_discount = free_units({free_units}) * rate({item_rate}) "
            f"= {item_discount}"
        )

        total_discount += item_discount

    frappe.msgprint(f"✅ DEBUG: total_discount FINAL = {total_discount}")
    return total_discount


def apply_fixed_price(promo, items_by_code):
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
    if not promo.discount_amount:
        return 0

    applicable_codes = resolve_applicable_item_codes(promo, items_by_code)
    has_items = any(items_by_code.get(code) for code in applicable_codes)

    if not has_items:
        return 0

    return promo.discount_amount
