import random
import time

import frappe
from frappe.tests.utils import FrappeTestCase


class TestLeadClassificationFlow(FrappeTestCase):
	"""Validate Lead classification lifecycle and propagation."""

	def setUp(self):
		timestamp = int(time.time() * 1000)
		random_suffix = random.randint(100, 999)
		self.phone_number = f"9{timestamp}{random_suffix}"[:15]

		self.lead_1 = None
		self.lead_2 = None
		self.contact = None
		self.customer = None

	def tearDown(self):
		for record in [self.lead_1, self.lead_2, self.customer]:
			if record:
				frappe.delete_doc_if_exists(record.doctype, record.name, force=True)

		if self.contact:
			frappe.delete_doc_if_exists("Contact", self.contact.name, force=True)

		frappe.db.commit()

	def test_first_lead_is_nuevo_at_creation_time(self):
		"""
		First Lead must be classified as Nuevo at insert time.
		Nuevo is NOT guaranteed to persist after save/reload.
		"""
		self.lead_1 = frappe.get_doc(
			{
				"doctype": "Lead",
				"first_name": "First Lead",
				"phone": self.phone_number,
				"custom_person_qty": 3,
				"custom_has_hotel_voucher": 1,
				"is_corpo": 0,
			}
		)

		self.lead_1.insert(ignore_permissions=True)

		categories = [row.customer_category for row in self.lead_1.custom_customer_category]

		self.assertIn("Nuevo", categories)
		self.assertNotIn("Recurrente", categories)

	def test_first_lead_creates_contact(self):
		"""
		First Lead must create a Contact with the same phone.
		"""
		self.lead_1 = frappe.get_doc(
			{
				"doctype": "Lead",
				"first_name": "First Lead",
				"phone": self.phone_number,
			}
		).insert(ignore_permissions=True)

		contact_name = frappe.db.get_value("Contact", {"phone": self.phone_number}, "name")
		self.assertTrue(contact_name)

		self.contact = frappe.get_doc("Contact", contact_name)

	def test_second_lead_is_recurrente_and_updates_contact_and_customer(self):
		"""
		Second Lead for the same phone must classify everything as Recurrente.
		"""
		self.lead_1 = frappe.get_doc(
			{"doctype": "Lead", "first_name": "First Lead", "phone": self.phone_number}
		).insert(ignore_permissions=True)

		contact_name = frappe.db.get_value("Contact", {"phone": self.phone_number}, "name")
		self.contact = frappe.get_doc("Contact", contact_name)

		self.customer = frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": "Test Customer",
				"customer_primary_contact": self.contact.name,
			}
		).insert(ignore_permissions=True)

		self.lead_2 = frappe.get_doc(
			{"doctype": "Lead", "first_name": "Second Lead", "phone": self.phone_number}
		).insert(ignore_permissions=True)

		self.lead_2.reload()
		self.contact.reload()
		self.customer.reload()

		self.assertEqual([r.customer_category for r in self.lead_2.custom_customer_category], ["Recurrente"])
		self.assertEqual([r.customer_category for r in self.contact.custom_customer_category], ["Recurrente"])
		self.assertEqual(
			[r.customer_category for r in self.customer.custom_customer_category], ["Recurrente"]
		)
