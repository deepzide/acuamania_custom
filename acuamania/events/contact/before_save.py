from acuamania.events.contact.normalize_contact_phone import normalize_contact_phone
from acuamania.events.contact.sync_custom_email import sync_custom_email
from acuamania.events.contact.contact_propagation.contact_propagation import contact_propagation


def before_save(doc, method=None):
    normalize_contact_phone(doc)
    sync_custom_email(doc)