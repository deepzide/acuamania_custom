from acuamania.events.sales_order.sync_custom_email import sync_custom_email


def before_save(doc, method=None):
    sync_custom_email(doc)