import frappe

from acuamania.patches.hide_fields import FIELDS_TO_HIDE, hide_fields


def _get_docfield(doctype: str, fieldname: str):
	docfield_name = frappe.db.exists(
		"DocField",
		{
			"parent": doctype,
			"fieldname": fieldname,
		},
	)
	if not docfield_name:
		return None

	return frappe.get_doc("DocField", docfield_name)


def test_hide_fields_patch():
	"""
	Ensures that all configured fields are hidden
	after running the hide_fields patch function.
	"""

	hide_fields(FIELDS_TO_HIDE)
	frappe.db.commit()

	for doctype, fieldnames in FIELDS_TO_HIDE.items():
		for fieldname in fieldnames:
			docfield = _get_docfield(doctype, fieldname)

			assert docfield is not None, f"DocField '{fieldname}' not found in {doctype}"

			assert docfield.hidden == 1, f"DocField '{fieldname}' in {doctype} is not hidden"
