from acuamania.events.sales_order.create_sales_invoice_from_sales_order import (
	create_sales_invoice_from_sales_order,
)


def on_submit(doc, method=None):
	create_sales_invoice_from_sales_order(doc)
