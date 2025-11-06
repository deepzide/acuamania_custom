import frappe


def create_custom_field(field_data: dict, doctype: str):
    """Create a Custom Field in a given DocType using explicit field data (includes insert_after)."""
    fieldname = field_data.get("fieldname")
    if not fieldname:
        frappe.throw("Field data must include 'fieldname'")

    if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname}):
        frappe.logger().info(f"Field '{fieldname}' already exists in {doctype}.")
        return

    field_doc = {"doctype": "Custom Field", "dt": doctype, **field_data}
    frappe.get_doc(field_doc).insert(ignore_permissions=True)
    frappe.logger().info(f"✅ Created custom field '{fieldname}' in {doctype}.")
