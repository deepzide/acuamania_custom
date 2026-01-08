from acuamania.events.customer.set_contact_person import set_contact_person


def before_insert(doc, method=None):
    set_contact_person(doc)