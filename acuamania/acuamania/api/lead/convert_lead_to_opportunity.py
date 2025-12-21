import frappe
from erpnext.crm.doctype.lead.lead import make_opportunity as make_opportunity_from_lead


@frappe.whitelist()
def convert_lead_to_opportunity(lead_name):
	"""
	Create and insert an Opportunity from a Lead,
	reusing ERPNext core logic.
	"""
	if not lead_name:
		frappe.throw("Lead name is required")

	if not frappe.db.exists("Lead", lead_name):
		frappe.throw(f"Lead '{lead_name}' does not exist")

	try:
		opportunity_doc = make_opportunity_from_lead(source_name=lead_name)

		opportunity_doc.insert(ignore_permissions=True)

		return opportunity_doc.name

	except Exception:
		frappe.log_error(
			title="Error creating Opportunity from Lead",
			message=frappe.get_traceback(),
		)
		frappe.throw("Failed to create Opportunity from Lead")
