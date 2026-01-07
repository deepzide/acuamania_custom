import frappe


STATUS_CATEGORIES = {"Nuevo", "Recurrente"}
RESIDENT_CATEGORY = "Residente"
GROUP_CATEGORY = "Grupo"
CORPORATE_CATEGORY = "Corporativo"
HOTEL_CATEGORY = "Hotel"

def classify_customer_status(doc):
	"""
	Clasifica como Nuevo/Recurrente.
	Atomizado para ejecutarse desde cualquier hook.
	"""
	phone_number = (doc.phone or "").strip()
	if not phone_number:
		return

	contact_exists = frappe.db.exists("Contact", {"phone": phone_number})
	status = "Recurrente" if contact_exists else "Nuevo"

	_apply_to_lead(doc, {status})


def classify_group(doc):
	custom_person_qty = getattr(doc, "custom_person_qty", 1)

	if custom_person_qty > 1:
		_apply_to_lead(doc, {GROUP_CATEGORY})

	if custom_person_qty <= 1:
		_remove_category(doc, GROUP_CATEGORY)


def classify_corporate(doc):
	is_corpo = getattr(doc, "is_corpo", 0)

	if is_corpo:
		_apply_to_lead(doc, {CORPORATE_CATEGORY})

	if not is_corpo:
		_remove_category(doc, CORPORATE_CATEGORY)


def classify_hotel(doc):
	is_hotel = getattr(doc, "custom_has_hotel_voucher", 0)

	if is_hotel:
		_apply_to_lead(doc, {HOTEL_CATEGORY})

	if not is_hotel:
		_remove_category(doc, HOTEL_CATEGORY)


def classify_resident(doc):
	if _is_resident_territory(doc):
		_apply_to_lead(doc, {RESIDENT_CATEGORY})

	if not _is_resident_territory(doc):
		_remove_category(doc, RESIDENT_CATEGORY)


def _is_resident_territory(doc):
	territory = getattr(doc, "territory", None) or getattr(doc, "custom_territory", None)
	if not territory:
		return False

	is_resident = frappe.db.get_value("Territory", territory, "custom_is_resident")
	return bool(is_resident)


def _apply_to_lead(lead_doc, categories):
	for category in categories:
		if category in STATUS_CATEGORIES:
			_set_exclusive_status(lead_doc, category)
		else:
			_append_if_missing(lead_doc, category)


def _set_exclusive_status(doc, status):
	opposite = "Recurrente" if status == "Nuevo" else "Nuevo"

	preserved = [r for r in doc.custom_customer_category if r.customer_category != opposite]

	doc.set("custom_customer_category", preserved)

	if not any(r.customer_category == status for r in preserved):
		doc.append("custom_customer_category", {"customer_category": status})


def _append_if_missing(doc, category):
	existing = [r.customer_category for r in doc.custom_customer_category]
	if category not in existing:
		doc.append("custom_customer_category", {"customer_category": category})


def _remove_category(doc, category_name):
	for row in list(doc.custom_customer_category):
		if row.customer_category == category_name:
			doc.custom_customer_category.remove(row)
