from acuamania.events.sales_order.sync_custom_email import sync_custom_email
from acuamania.acuamania.promo_engine.engine import apply_selected_promotion


def before_save(doc, method=None):
    sync_custom_email(doc)
    apply_selected_promotion(doc)