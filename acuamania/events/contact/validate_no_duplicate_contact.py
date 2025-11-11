import frappe
from frappe import _


def validate_no_duplicate_contact(doc, method=None):
    """
    Validate that there are no duplicate contacts with the same phone number
    """
    if not doc.phone:
        return

    existing_contact = frappe.db.exists(
        "Contact",
        {
            "phone": doc.phone,
            "name": ("!=", doc.name)
        }
    )

    if existing_contact:
        frappe.throw(
            _("A contact with phone number {0} already exists").format(doc.phone),
            frappe.DuplicateEntryError
        )