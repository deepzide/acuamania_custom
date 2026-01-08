from acuamania.events.customer.ensure_contact_dynamic_link import ensure_contact_dynamic_link


def after_insert(doc, method=None):
    ensure_contact_dynamic_link(
        contact_name=doc.customer_primary_contact,
        party_doctype="Customer",
        party_name=doc.name,
    )