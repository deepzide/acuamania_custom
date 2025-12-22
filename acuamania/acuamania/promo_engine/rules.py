def resolve_applicable_item_codes(promo, items_by_code):
	"""
	Get which item codes are elegibles
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
	Applies a 'required x free' promotion.

	Returns:
	    (discount_amount, applied_qty)
	where applied_qty is the number of free units granted.
	"""
	required_qty, free_qty = _get_required_and_free_qty(promo)
	if not _is_valid_required_free(required_qty, free_qty):
		return 0, 0

	unit_prices = _extract_unit_prices(items_by_code)
	total_units = len(unit_prices)

	free_units = _calculate_free_units(total_units, required_qty, free_qty)
	if free_units <= 0:
		return 0, 0

	discount = _sum_cheapest_units(unit_prices, free_units)
	return discount, free_units


def apply_fixed_price(promo, items_by_code):
	"""
	Applies a fixed price promotion.

	Returns:
	    (discount_amount, applied_qty)
	where applied_qty is the number of units discounted.
	"""
	if not promo.fixed_price:
		return 0, 0

	applicable_codes = resolve_applicable_item_codes(promo, items_by_code)

	total_discount = 0
	applied_qty = 0

	for code in applicable_codes:
		for row in items_by_code.get(code, []):
			if not row.qty or not row.rate:
				continue

			if row.rate <= promo.fixed_price:
				continue

			unit_discount = row.rate - promo.fixed_price
			total_discount += unit_discount * row.qty
			applied_qty += row.qty

	return total_discount, applied_qty


def apply_percentage_discount(promo, items_by_code):
	"""
	Applies a percentage discount promotion.

	Returns:
	    (discount_amount, applied_qty)
	where applied_qty is the number of units included in the discount base.
	"""
	if not promo.discount_percentage:
		return 0, 0

	applicable_codes = resolve_applicable_item_codes(promo, items_by_code)

	base_amount = 0
	applied_qty = 0

	for code in applicable_codes:
		for row in items_by_code.get(code, []):
			if not row.qty or not row.rate:
				continue

			base_amount += row.qty * row.rate
			applied_qty += row.qty

	if not base_amount:
		return 0, 0

	discount = base_amount * (promo.discount_percentage / 100.0)
	return discount, applied_qty


def apply_discount_amount(promo, items_by_code):
	"""
	Applies a flat discount amount promotion.

	Returns:
	    (discount_amount, applied_qty)
	applied_qty is always 1 if at least one applicable item exists.
	"""
	if not promo.discount_amount:
		return 0, 0

	applicable_codes = resolve_applicable_item_codes(promo, items_by_code)
	has_items = any(items_by_code.get(code) for code in applicable_codes)

	if not has_items:
		return 0, 0

	return promo.discount_amount, 1


def _get_required_and_free_qty(promo):
	return int(promo.required or 0), int(promo.free or 0)


def _is_valid_required_free(required_qty, free_qty):
	return required_qty > 0 and free_qty > 0


def _extract_unit_prices(items_by_code):
	"""
	Flattens all item rows into individual unit prices, quantity-aware.
	"""
	unit_prices = []

	for rows in items_by_code.values():
		for row in rows:
			qty = int(row.qty or 0)
			rate = float(row.rate or 0)

			if qty <= 0 or rate <= 0:
				continue

			unit_prices.extend([rate] * qty)

	return unit_prices


def _calculate_free_units(total_units, required_qty, free_qty):
	if total_units < required_qty:
		return 0

	return (total_units // required_qty) * free_qty


def _sum_cheapest_units(unit_prices, free_units):
	unit_prices.sort()
	return sum(unit_prices[:free_units])
