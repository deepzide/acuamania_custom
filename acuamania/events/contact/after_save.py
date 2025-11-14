from acuamania.events.contact.contact_propagation.contact_propagation import contact_propagation


def after_save(doc, method=None):
    contact_propagation(doc)
