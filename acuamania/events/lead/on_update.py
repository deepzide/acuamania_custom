from acuamania.events.lead.propagate_classifications import propagate_classifications


def on_update(doc, method=None):
    propagate_classifications(doc)