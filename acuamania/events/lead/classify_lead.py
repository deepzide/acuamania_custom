from acuamania.events.utils import classify_group, classify_customer_status, classify_resident
from acuamania.utils.sync import with_sync_guard

@with_sync_guard
def classify_lead(doc):
	"""
	Classify Lead categories.
	"""
	classify_customer_status(doc)
	classify_group(doc)
	classify_resident(doc)

@with_sync_guard
def classify_lead_before_save(doc):
	"""
	Classify Lead categories before save.
	"""
	classify_group(doc)
	classify_resident(doc)
