import frappe


def set_contact_person(doc):
    if not doc.contact_person and doc.phone:
        contact = frappe.get_doc("Contact", {"phone": doc.phone})
        if not contact:
            return
        
        doc.contact_person = contact.name
        doc.contact_email = contact.email_id