import frappe
from frappe.utils import now

from acuamania.events.contact.contact_propagation.config import CONTACT_FIELD_MAPPING, CONTACT_LINK_FIELDS
from acuamania.utils.sync import with_sync_guard


@with_sync_guard
def contact_propagation(contact_doc, method=None):
	"""Propagate Contact fields (source, territory, email, etc.) to all linked doctypes."""

	for target_doctype, link_def in CONTACT_LINK_FIELDS.items():
		_sync_linked_docs(contact_doc, target_doctype, link_def)


def _sync_linked_docs(contact_doc, target_doctype, link_def):
	"""Find and update all draft documents linked to the Contact."""
	link_field = link_def.get("field")
	if not link_field:
		return

	link_value = contact_doc.name if link_field == "contact_person" else contact_doc.phone
	if not link_value:
		return

	if target_doctype == "Lead" and getattr(frappe.flags, "skip_contact_to_lead_sync", False):
		return

	related_docs = frappe.get_all(
		target_doctype,
		filters={link_field: link_value, "docstatus": 0},
		pluck="name",
	)

	if not related_docs:
		return

	mapping = CONTACT_FIELD_MAPPING.get(target_doctype, {})
	contact_data = contact_doc.as_dict()

	for doc_name in related_docs:
		try:
			_apply_field_mapping(contact_doc, target_doctype, doc_name, mapping, contact_data)
		except Exception as e:
			frappe.log_error(
				title=f"Contact Sync Error - {contact_doc.name}",
				message=f"Failed updating {target_doctype} {doc_name}: {e}",
			)


def _apply_field_mapping(contact_doc, target_doctype, doc_name, mapping, contact_data):
	"""Apply field mappings if values differ and persist the changes."""
	doc = frappe.get_doc(target_doctype, doc_name)
	updated = False

	for target_field, source_field in mapping.items():
		new_value = contact_data.get(source_field)
		if new_value is None:
			continue

		if doc.get(target_field) != new_value:
			doc.set(target_field, new_value)
			updated = True

	if updated:
		reset_skip_flag = False
		previous_skip_flag = getattr(frappe.flags, "skip_lead_to_contact_sync", False)
		if target_doctype == "Lead":
			frappe.flags.skip_lead_to_contact_sync = True
			reset_skip_flag = True

		try:
			doc.save(ignore_permissions=True)
		finally:
			if reset_skip_flag:
				frappe.flags.skip_lead_to_contact_sync = previous_skip_flag

		frappe.logger("contact_sync").info(
			f"🔄 Updated {target_doctype} {doc_name} from Contact {contact_doc.name} at {now()}"
		)
