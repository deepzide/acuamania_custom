from acuamania.acuamania.promo_engine.engine import apply_selected_promotion
from acuamania.acuamania.promo_engine.set_default_group_promo import set_default_group_promo


def before_save(doc, method=None):
    set_default_group_promo(doc)
    apply_selected_promotion(doc)