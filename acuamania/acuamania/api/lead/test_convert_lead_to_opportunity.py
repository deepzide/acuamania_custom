import frappe
from frappe.tests.utils import FrappeTestCase

from acuamania.acuamania.api.lead.convert_lead_to_opportunity import convert_lead_to_opportunity


class TestMakeOpportunityFromLead(FrappeTestCase):
	"""Test custom API that creates and inserts Opportunity from Lead."""

	def setUp(self):
		"""Create a Lead used for the test."""
		self.lead = frappe.get_doc(
			{
				"doctype": "Lead",
				"first_name": "Test",
				"last_name": "Lead",
				"company_name": "Test Company",
				"email_id": "test.lead@example.com",
				"phone": "099000999",
				"status": "Open",
			}
		).insert(ignore_permissions=True)

		self.opportunity_name = None

	def tearDown(self):
		"""Delete only records created by this test."""
		if self.opportunity_name:
			frappe.delete_doc_if_exists(
				"Opportunity",
				self.opportunity_name,
				force=True,
			)

		if self.lead:
			frappe.delete_doc_if_exists(
				"Lead",
				self.lead.name,
				force=True,
			)

		frappe.db.commit()

	def test_convert_lead_to_opportunity(self):
		"""Should create and insert an Opportunity from a Lead."""

		self.opportunity_name = convert_lead_to_opportunity(self.lead.name)

		self.assertTrue(self.opportunity_name)

		opportunity = frappe.get_doc("Opportunity", self.opportunity_name)

		self.assertEqual(opportunity.opportunity_from, "Lead")
		self.assertEqual(opportunity.party_name, self.lead.name)
		self.assertEqual(opportunity.status, "Open")
