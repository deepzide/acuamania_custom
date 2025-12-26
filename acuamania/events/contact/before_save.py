from acuamania.events.contact.normalize_contact_phone import normalize_contact_phone
from acuamania.events.contact.sync_custom_email import sync_custom_email
from acuamania.events.lead.classify_lead import classify_lead_before_save


def before_save(doc, method=None):
	normalize_contact_phone(doc)
	sync_custom_email(doc)
