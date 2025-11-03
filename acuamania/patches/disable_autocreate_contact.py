import frappe

DOCTYPE = "CRM Settings"

def execute():
    """Disable auto creation of Contact in CRM Settings."""
    try:
        crm_settings = frappe.get_single(DOCTYPE)
        crm_settings.auto_creation_of_contact = 0
        crm_settings.save(ignore_permissions=True)
        frappe.db.commit()
        frappe.logger().info("✅ Auto creation of Contact disabled in CRM Settings.")
    except Exception as e:
        frappe.log_error(message=str(e), title="CRM Settings Patch Failed")
