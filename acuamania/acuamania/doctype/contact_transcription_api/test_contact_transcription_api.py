# Copyright (c) 2025, cegomezpy and Contributors
# See license.txt

# import frappe
from frappe.tests.utils import FrappeTestCase


class TestContactTranscriptionAPI(FrappeTestCase):
	pass
# Copyright (c) 2025
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

ENDPOINT = "acuamania.acuamania.doctype.contact_transcription_api.contact_transcription_api.append_transcription"


class TestContactTranscriptionAPI(FrappeTestCase):

    def setUp(self):
        # Create test contact with test phone
        self.contact = frappe.get_doc({
            "doctype": "Contact",
            "first_name": "Test User",
            "phone_nos": [{"phone": "099111222"}],
            "custom_transcription_text": ""
        }).insert(ignore_permissions=True)

        self.endpoint = frappe.get_attr(ENDPOINT)

    def test_append_creates_buffer(self):
        self.endpoint(phone="099111222", message="Hola")

        c = frappe.get_doc("Contact", self.contact.name)
        self.assertEqual(c.custom_transcription_text, "Hola")

    def test_append_appends_buffer(self):
        self.endpoint(phone="099111222", message="Hola")
        self.endpoint(phone="099111222", message="Mundo")

        c = frappe.get_doc("Contact", self.contact.name)
        self.assertEqual(c.custom_transcription_text, "Hola\nMundo")

    def test_ignore_if_no_contact(self):
        result = self.endpoint(phone="00000000", message="Hola")

        self.assertEqual(result["status"], "ignored")
        self.assertEqual(result["reason"], "Contact not found for this phone")
