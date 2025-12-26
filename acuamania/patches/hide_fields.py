import frappe

FIELDS_TO_HIDE = {
	"Quotation": ["base_in_words", "in_words"],
	"Sales Order": ["base_in_words", "in_words"],
	"Sales Invoice": ["base_in_words", "in_words"],
	"Lead": ["mobile_no"],
}


def hide_fields(fields_by_doctype: dict[str, list[str]]) -> None:
	"""
	Hides DocField entries for the given mapping of
	doctype -> list of fieldnames.

	The operation is idempotent and safe to run multiple times.
	"""

	for doctype, fieldnames in fields_by_doctype.items():
		for fieldname in fieldnames:
			docfield_name = frappe.db.exists(
				"DocField",
				{
					"parent": doctype,
					"fieldname": fieldname,
				},
			)

			if not docfield_name:
				frappe.logger().warning(f"Field '{fieldname}' not found in {doctype}. Skipping.")
				continue

			docfield = frappe.get_doc("DocField", docfield_name)

			if docfield.hidden:
				frappe.logger().info(f"Field '{fieldname}' already hidden in {doctype}. Skipping.")
				continue

			docfield.hidden = 1
			docfield.save(ignore_permissions=True)

			frappe.logger().info(f"✅ Field '{fieldname}' set to hidden in {doctype}.")


def execute():
	try:
		hide_fields(FIELDS_TO_HIDE)
		frappe.db.commit()

	except Exception as exc:
		frappe.log_error(
			message=str(exc),
			title="Failed to hide configured DocFields",
		)
