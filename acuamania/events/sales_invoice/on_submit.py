from acuamania.events.sales_invoice.create_two_payment_entries import create_two_payment_entries


def on_submit(doc, method=None):
	create_two_payment_entries(doc)