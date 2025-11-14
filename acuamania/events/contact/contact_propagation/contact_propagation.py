import frappe
from frappe.utils import now
from acuamania.events.contact.contact_propagation.config import CONTACT_LINK_FIELDS, CONTACT_FIELD_MAPPING


def contact_propagation(contact_doc, method=None):
    """Propagate Contact fields (source, territory, email, etc.) to all linked doctypes."""
    if frappe.flags.in_patch or frappe.flags.in_migrate:
        return

    if frappe.flags.get("skip_contact_sync"):
        return

    frappe.flags.skip_contact_sync = True
    try:
        for target_doctype, link_def in CONTACT_LINK_FIELDS.items():
            _sync_linked_docs(contact_doc, target_doctype, link_def)
    finally:
        frappe.flags.skip_contact_sync = False


def _sync_linked_docs(contact_doc, target_doctype, link_def):
    """Find and update all draft documents linked to the Contact."""
    link_field = link_def.get("field")
    if not link_field:
        return

    link_value = contact_doc.name if link_field == "contact_person" else contact_doc.phone
    if not link_value:
        return

    related_docs = frappe.get_all(
        target_doctype,
        filters={link_field: link_value, "docstatus": 0},
        pluck="name",
    )

    if not related_docs:
        return

    mapping = CONTACT_FIELD_MAPPING.get(target_doctype, {})
    contact_data = contact_doc.as_dict()

    for doc_name in related_docs:
        try:
            _apply_field_mapping(contact_doc, target_doctype, doc_name, mapping, contact_data)
        except Exception as e:
            frappe.log_error(
                title=f"Contact Sync Error - {contact_doc.name}",
                message=f"Failed updating {target_doctype} {doc_name}: {e}",
            )


def _apply_field_mapping(contact_doc, target_doctype, doc_name, mapping, contact_data):
    """Apply field mappings if values differ and persist the changes."""
    doc = frappe.get_doc(target_doctype, doc_name)
    updated = False

    for target_field, source_field in mapping.items():
        new_value = contact_data.get(source_field)
        if new_value is None:
            continue
        if doc.get(target_field) != new_value:
            doc.set(target_field, new_value)
            updated = True

    if updated:
        doc.save(ignore_permissions=True)
        frappe.logger("contact_sync").info(
            f"🔄 Updated {target_doctype} {doc_name} from Contact {contact_doc.name} at {now()}"
        )
