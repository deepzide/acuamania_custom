from acuamania.events.lead.classify_lead import is_new_or_recurrent


def before_save(doc, method=None):
    is_new_or_recurrent(doc)