# Copyright (c) 2024, Acuamania and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = get_columns()
	data, notes = get_data(filters)

	if notes:
		for note in notes:
			data.append({"metric": note, "value": "", "detalle": ""})

	return columns, data


def get_columns():
	return [
		{"fieldname": "metric", "label": _("Métrica"), "fieldtype": "Data", "width": 260},
		{"fieldname": "value", "label": _("Valor"), "fieldtype": "Float", "precision": 2, "width": 120},
		{"fieldname": "detalle", "label": _("Detalle"), "fieldtype": "Data", "width": 420},
	]


def get_data(filters):
	notes = []

	leads = get_leads(filters, notes)
	lead_count = len(leads)

	opp_count = get_opportunity_count(leads, filters)
	quot_count = get_quotation_count(leads, filters)
	order_count = get_order_count(leads, filters)

	lead_to_opp = pct(opp_count, lead_count)
	opp_to_quot = pct(quot_count, opp_count)
	quot_to_order = pct(order_count, quot_count)
	lead_to_order = pct(order_count, lead_count)

	data = [
		{"metric": _("Leads"), "value": lead_count, "detalle": _("Registros en el rango de fechas filtrado")},
		{"metric": _("Oportunidades"), "value": opp_count, "detalle": _("Oportunidades creadas desde Lead")},
		{"metric": _("Cotizaciones"), "value": quot_count, "detalle": _("Cotizaciones de Leads (status cualquiera)")},
		{"metric": _("Órdenes de Venta"), "value": order_count, "detalle": _("Órdenes generadas desde Cotizaciones de Leads")},
		{"metric": _("Tasa Lead → Oportunidad"), "value": lead_to_opp, "detalle": _("Oportunidades / Leads * 100")},
		{"metric": _("Tasa Oportunidad → Cotización"), "value": opp_to_quot, "detalle": _("Cotizaciones / Oportunidades * 100")},
		{"metric": _("Tasa Cotización → Orden"), "value": quot_to_order, "detalle": _("Órdenes / Cotizaciones * 100")},
		{"metric": _("Tasa global Lead → Orden"), "value": lead_to_order, "detalle": _("Órdenes / Leads * 100")},
	]

	return data, notes


def get_leads(filters, notes):
	conditions = []
	params = {}

	if filters.get("from_date"):
		conditions.append("date(creation) >= %(from_date)s")
		params["from_date"] = filters.from_date

	if filters.get("to_date"):
		conditions.append("date(creation) <= %(to_date)s")
		params["to_date"] = filters.to_date

	if filters.get("channel"):
		conditions.append("source = %(channel)s")
		params["channel"] = filters.channel

	customer_type = filters.get("customer_type")
	if customer_type:
		customer_type_field = get_customer_type_field()
		if customer_type_field:
			conditions.append(f"{customer_type_field} = %(customer_type)s")
			params["customer_type"] = customer_type
		else:
			notes.append(_("El filtro de tipo de cliente no está disponible en Lead en esta instalación."))

	where_clause = " and ".join(conditions) if conditions else "1=1"
	return frappe.db.sql(
		f"""select name from `tabLead` where {where_clause}""",
		params,
		as_dict=0,
	)


def get_opportunity_count(leads, filters):
	if not leads:
		return 0

	conditions = ["opportunity_from = 'Lead'", "party_name in %(lead_names)s"]
	params = {"lead_names": tuple(l[0] for l in leads)}

	if filters.get("from_date"):
		conditions.append("date(creation) >= %(from_date)s")
		params["from_date"] = filters.from_date

	if filters.get("to_date"):
		conditions.append("date(creation) <= %(to_date)s")
		params["to_date"] = filters.to_date

	if filters.get("channel") and frappe.db.has_column("Opportunity", "source"):
		conditions.append("source = %(channel)s")
		params["channel"] = filters.channel

	where_clause = " and ".join(conditions)
	return frappe.db.sql(
		f"""select count(name) from `tabOpportunity` where {where_clause}""",
		params,
	)[0][0]


def get_quotation_count(leads, filters):
	if not leads:
		return 0

	conditions = [
		"quotation_to = 'Lead'",
		"party_name in %(lead_names)s",
	]
	params = {"lead_names": tuple(l[0] for l in leads)}

	if filters.get("from_date"):
		conditions.append("date(transaction_date) >= %(from_date)s")
		params["from_date"] = filters.from_date

	if filters.get("to_date"):
		conditions.append("date(transaction_date) <= %(to_date)s")
		params["to_date"] = filters.to_date

	where_clause = " and ".join(conditions)
	return frappe.db.sql(
		f"""select count(name) from `tabQuotation` where {where_clause}""",
		params,
	)[0][0]


def get_order_count(leads, filters):
	if not leads:
		return 0

	conditions = [
		"so.customer in (select customer from `tabQuotation` where quotation_to = 'Lead' and party_name in %(lead_names)s)",
	]
	params = {"lead_names": tuple(l[0] for l in leads)}

	if filters.get("from_date"):
		conditions.append("date(so.transaction_date) >= %(from_date)s")
		params["from_date"] = filters.from_date

	if filters.get("to_date"):
		conditions.append("date(so.transaction_date) <= %(to_date)s")
		params["to_date"] = filters.to_date

	where_clause = " and ".join(conditions)
	return frappe.db.sql(
		f"""select count(name) from `tabSales Order` so where {where_clause}""",
		params,
	)[0][0]


def pct(numerator, denominator):
	return flt(numerator) / flt(denominator or 1.0) * 100.0


def get_customer_type_field():
	for candidate in ("customer_group", "customer_type"):
		if frappe.db.has_column("Lead", candidate):
			return candidate
	return ""
