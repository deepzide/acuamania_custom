import frappe

LEAD_DOCTYPE = "Lead"
FIELDNAME = "custom_contact_name"
FIELD_LABEL = "Contact Name"
FIELD_TYPE = "Link"
FIELD_OPTIONS = "Contact"

def execute():
    """Add custom_contact_name field to Lead if not exists."""
    try:
        if frappe.db.exists("Custom Field", {"dt": LEAD_DOCTYPE, "fieldname": FIELDNAME}):
            frappe.logger().info(f"Custom field '{FIELDNAME}' already exists in {LEAD_DOCTYPE}.")
            return

        custom_field = frappe.get_doc({
            "doctype": "Custom Field",
            "dt": LEAD_DOCTYPE,
            "fieldname": FIELDNAME,
            "label": FIELD_LABEL,
            "fieldtype": FIELD_TYPE,
            "options": FIELD_OPTIONS,
            "insert_after": "email_id",
            "read_only": 0,
            "hidden": 0
        })

        custom_field.insert(ignore_permissions=True)
        frappe.db.commit()
        frappe.logger().info(f"✅ Custom field '{FIELDNAME}' created successfully in {LEAD_DOCTYPE}.")
    except Exception as e:
        frappe.log_error(message=str(e), title=f"Failed to create {FIELDNAME} in {LEAD_DOCTYPE}")
