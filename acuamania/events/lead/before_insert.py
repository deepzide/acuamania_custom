from acuamania.events.lead.classify_lead import classify_lead


def before_insert(doc, method=None):
	classify_lead(doc)
