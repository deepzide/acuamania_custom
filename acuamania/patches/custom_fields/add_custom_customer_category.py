import frappe

FIELDNAME = "custom_customer_category"
LABEL = "Customer Category"
FIELD_TYPE = "Table MultiSelect"
OPTIONS = "Customer__Customer_Category"
INSERT_AFTER = "customer_name"
TARGET_DOCTYPES = ["Customer", "Contact", "Lead"]

def execute():
    try:
        for doctype in TARGET_DOCTYPES:
            if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": FIELDNAME}):
                frappe.logger().info(f"Field '{FIELDNAME}' already exists in {doctype}.")
                continue

            custom_field = frappe.get_doc({
                "doctype": "Custom Field",
                "dt": doctype,
                "fieldname": FIELDNAME,
                "label": LABEL,
                "fieldtype": FIELD_TYPE,
                "options": OPTIONS,
                "insert_after": INSERT_AFTER,
                "reqd": 0,
                "hidden": 0,
                "no_copy": 0,
                "allow_in_quick_entry": 0
            })
            custom_field.insert(ignore_permissions=True)
            frappe.logger().info(f"✅ Field '{FIELDNAME}' created successfully in {doctype}.")

        frappe.db.commit()
    except Exception as e:
        frappe.log_error(message=str(e), title="Failed to create Customer Classification field")
