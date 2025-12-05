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
    Nueva lógica:
    - Sumar cantidades de TODOS los item_codes aplicables.
    - Determinar cuántos grupos (required) entran.
    - free_units = groups * free
    - El valor gratis siempre es el ítem de menor rate entre todos los aplicables.
    """

    frappe.msgprint("🔵 DEBUG: Entrando a apply_required_x_free()")

    required = promo.required
    free = promo.free

    frappe.msgprint(f"🔵 DEBUG: required={required}, free={free}")

    if not required or required <= 0:
        return 0
    if free is None or free < 0:
        return 0

    applicable_codes = resolve_applicable_item_codes(promo, items_by_code)
    frappe.msgprint(f"🔵 DEBUG: applicable_codes = {applicable_codes}")

    # 1) Sumar cantidades TOTAL entre todos los códigos
    total_qty = 0
    all_rates = []

    for code in applicable_codes:
        rows = items_by_code.get(code, [])
        for row in rows:
            qty = row.qty or 0
            rate = row.rate or 0
            total_qty += qty
            all_rates.append(rate)

    frappe.msgprint(f"🔵 DEBUG: total_qty sumado entre todos los ítems = {total_qty}")
    frappe.msgprint(f"🔵 DEBUG: all_rates = {all_rates}")

    if total_qty < required:
        frappe.msgprint("🟡 DEBUG: total_qty < required → no aplica")
        return 0

    # 2) Calcular grupos
    groups = total_qty // required
    free_units = groups * free

    frappe.msgprint(f"🔵 DEBUG: groups={groups}, free_units={free_units}")

    if free_units <= 0:
        frappe.msgprint("🟡 DEBUG: free_units <= 0 → no descuento")
        return 0

    # 3) Encontrar la entrada más barata
    min_rate = min(all_rates) if all_rates else 0

    frappe.msgprint(f"🔵 DEBUG: min_rate entre TODOS los ítems aplicables = {min_rate}")

    if min_rate <= 0:
        frappe.msgprint("🟡 DEBUG: min_rate <= 0 → no descuento")
        return 0

    # 4) Calcular descuento total
    total_discount = min_rate * free_units

    frappe.msgprint(
        f"🟣 DEBUG: total_discount = min_rate({min_rate}) * free_units({free_units}) "
        f"= {total_discount}"
    )

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
