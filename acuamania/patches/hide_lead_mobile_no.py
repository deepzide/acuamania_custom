import frappe

LEAD_DOCTYPE = "Lead"
FIELDNAME = "mobile_no"


def execute():
	try:
		docfield_name = frappe.db.exists("DocField", {"parent": LEAD_DOCTYPE, "fieldname": FIELDNAME})
		if not docfield_name:
			frappe.logger().warning(f"Field '{FIELDNAME}' not found in {LEAD_DOCTYPE}.")
			return
		docfield = frappe.get_doc("DocField", docfield_name)
		docfield.hidden = 1
		docfield.save(ignore_permissions=True)
		frappe.db.commit()
		frappe.logger().info(f"✅ Field '{FIELDNAME}' set to hidden in {LEAD_DOCTYPE}.")
	except Exception as e:
		frappe.log_error(message=str(e), title=f"Failed to hide {FIELDNAME} in {LEAD_DOCTYPE}")
