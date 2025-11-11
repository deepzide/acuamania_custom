

def sync_custom_email(doc, method=None):
    """Sync Contact.custom_email → Contact.email_id before saving."""
    if not hasattr(doc, "custom_email"):
        return

    custom_email = (doc.custom_email or "").strip()
    if not custom_email:
        return

    if custom_email != (doc.email_id or "").strip():
        doc.email_id = custom_email
