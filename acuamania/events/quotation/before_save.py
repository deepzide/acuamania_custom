from acuamania.acuamania.promo_engine.engine import apply_selected_promotion


def before_save(doc, method=None):
	apply_selected_promotion(doc)
