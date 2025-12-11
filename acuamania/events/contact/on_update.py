import frappe
from acuamania.events.contact.contact_propagation.contact_propagation import contact_propagation


def on_update(doc, method=None):
    contact_propagation(doc)
