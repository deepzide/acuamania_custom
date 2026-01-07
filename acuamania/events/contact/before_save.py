from acuamania.events.contact.normalize_contact_phone import normalize_contact_phone
from acuamania.events.contact.sync_custom_email import sync_custom_email
from acuamania.events.contact.classify_contact import classify_contact

def before_save(doc, method=None):
	classify_contact(doc)
	normalize_contact_phone(doc)
	sync_custom_email(doc)
