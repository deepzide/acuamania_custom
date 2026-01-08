import frappe

frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("set_contact_person", file_count=50)

def set_contact_person(doc):
    if not doc.customer_primary_contact and doc.lead_name:
        lead = frappe.get_doc("Lead", doc.lead_name)
        if not lead:
            return
        
        doc.customer_primary_contact = lead.custom_contact_name
    logger.debug(f"Set Customer.customer_primary_contact for {doc.name} from Lead {lead.name}: {lead.custom_contact_name}")