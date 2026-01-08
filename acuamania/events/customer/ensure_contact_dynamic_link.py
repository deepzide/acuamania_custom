import frappe

def ensure_contact_dynamic_link(contact_name: str, party_doctype: str, party_name: str):
    if not frappe.db.exists(
        "Dynamic Link",
        {
            "parenttype": "Contact",
            "parent": contact_name,
            "link_doctype": party_doctype,
            "link_name": party_name,
        },
    ):
        frappe.get_doc(
            {
                "doctype": "Dynamic Link",
                "parenttype": "Contact",
                "parentfield": "links",
                "parent": contact_name,
                "link_doctype": party_doctype,
                "link_name": party_name,
            }
        ).insert(ignore_permissions=True)
