from acuamania.events.lead.propagate_classifications import propagate_classifications
from acuamania.events.lead.upsert_contact import upsert_contact


def after_insert(doc, method=None):
	upsert_contact(doc, method)
	propagate_classifications(doc)
