import frappe


def create_sales_invoice_from_sales_order(doc, method=None):
	try:
		invoice_dict = frappe.call(
			"erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice", source_name=doc.name
		)

		invoice = frappe.get_doc(invoice_dict)

		invoice.insert(ignore_permissions=True)
		invoice.submit()

		frappe.msgprint(f"Sales Invoice {invoice.name} creado automáticamente desde Sales Order {doc.name}")

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error creando Sales Invoice desde Sales Order")
		frappe.throw(f"Ocurrió un error al generar la factura: {e}")
