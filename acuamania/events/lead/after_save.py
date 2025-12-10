from acuamania.events.lead.propagate_classifications import propagate_classifications


def after_save(doc, method=None):
    propagate_classifications(doc)