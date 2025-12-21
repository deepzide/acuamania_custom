from acuamania.events.lead.classify_lead import classify_lead_before_save


def before_save(doc, method=None):
	classify_lead_before_save(doc)
