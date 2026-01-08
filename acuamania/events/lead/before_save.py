from acuamania.events.lead.classify_lead import classify_lead_before_save
from acuamania.events.lead.set_mobile_no import set_mobile_no

def before_save(doc, method=None):
	classify_lead_before_save(doc)
	set_mobile_no(doc)