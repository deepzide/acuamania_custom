CONTACT_LINK_FIELDS = {
    "Lead": {"field": "phone"},
    "Opportunity": {"field": "phone"},
    "Sales Order": {"field": "contact_person"},
    "Customer": {"field": "mobile_no"},
}

CONTACT_FIELD_MAPPING = {
    "Lead": {
        "first_name": "first_name",
        "last_name": "last_name",
        "email_id": "email_id",
        "source": "custom_source",
        "territory": "custom_territory",
        "is_corpo": "is_corpo",
        "custom_has_hotel_voucher": "custom_has_hotel_voucher",
        "custom_person_qty": "custom_person_qty",
        "custom_customer_category": "custom_customer_category",
    },
    "Opportunity": {
        "contact_email": "email_id",
        "contact_person": "name",
        "territory": "custom_territory",
    },
    "Sales Order": {
        "custom_email": "email_id",
        "contact_person": "name",
        "contact_display": "full_name",
        "source": "custom_source",
        "territory": "custom_territory",
    },
    "Customer": {
        "customer_name": "full_name",
        "email_id": "email_id",
        "customer_primary_contact": "name",
        "territory": "custom_territory",
    },
}
