import frappe


@frappe.whitelist()
def update_contact_fields(contact_name, fields):
    if not contact_name:
        frappe.throw("contact_name is required")

    if not fields:
        return

    doc = frappe.get_doc("Contact", contact_name)

    for fieldname, value in fields.items():
        if not frappe.get_meta("Contact").has_field(fieldname):
            continue
        doc.set(fieldname, value)

    doc.save(ignore_permissions=True)
