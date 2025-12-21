from acuamania.events.contact.validate_no_duplicate_contact import validate_no_duplicate_contact


def before_insert(doc, method=None) -> None:
	"""
	Frappe hook called before inserting a Contact document.
	Ensures no duplicate contact exists by delegating to validate_no_duplicate.
	"""
	validate_no_duplicate_contact(doc)
