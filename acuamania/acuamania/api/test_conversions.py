import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today


class TestConversionEndpoints(FrappeTestCase):
	"""
	Validate Lead → Opportunity → Quotation → Sales Order
	using Acuamania whitelisted conversion endpoints.
	"""

	def setUp(self):
		self.lead = None
		self.opportunity = None
		self.quotation = None
		self.sales_order = None

		self._ensure_company()

		self.lead = frappe.get_doc(
			{
				"doctype": "Lead",
				"first_name": "Test",
				"last_name": "Conversion",
				"email_id": "conversion@test.com",
				"phone": "099999999",
				"company": self.company,
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		for doc in [
			self.sales_order,
			self.quotation,
			self.opportunity,
			self.lead,
		]:
			if not doc:
				continue

			try:
				doc.reload()
				if hasattr(doc, "docstatus") and doc.docstatus == 1:
					doc.cancel()
			except Exception:
				pass

			frappe.delete_doc_if_exists(doc.doctype, doc.name, force=True)

		frappe.db.commit()

	def _ensure_company(self):
		company = frappe.defaults.get_user_default("Company")
		if company:
			self.company = company
			return

		self.company = frappe.get_all("Company", pluck="name")[0]

	def test_full_conversion_flow(self):
		"""
		Lead → Opportunity → Quotation → Sales Order
		"""

		# --------------------------------------------------
		# Lead → Opportunity
		# --------------------------------------------------
		opportunity_name = frappe.call(
			"acuamania.acuamania.api.conversions.make_opportunity_and_insert",
			source_name=self.lead.name,
		)

		self.opportunity = frappe.get_doc("Opportunity", opportunity_name)

		self.assertEqual(self.opportunity.opportunity_from, "Lead")
		self.assertEqual(self.opportunity.party_name, self.lead.name)

		# --------------------------------------------------
		# ✅ ADD ITEMS TO OPPORTUNITY
		# --------------------------------------------------
		item = self.opportunity.append("items", {})
		item.item_code = "ENTR-GRAL"
		item.qty = 2
		item.rate = 1000

		self.opportunity.save(ignore_permissions=True)

		# --------------------------------------------------
		# Opportunity → Quotation
		# --------------------------------------------------
		quotation_name = frappe.call(
			"acuamania.acuamania.api.conversions.make_quotation_and_insert",
			source_name=self.opportunity.name,
		)

		self.quotation = frappe.get_doc("Quotation", quotation_name)

		self.assertEqual(self.quotation.opportunity, self.opportunity.name)
		self.assertTrue(self.quotation.items)

		# --------------------------------------------------
		# ✅ SET DELIVERY DATE (REQUIRED FOR SALES ORDER)
		# --------------------------------------------------
		self.quotation.delivery_date = today()
		for row in self.quotation.items:
			row.delivery_date = today()
			row.schedule_date = today()

		self.quotation.save(ignore_permissions=True)

		# --------------------------------------------------
		# ✅ SUBMIT QUOTATION (ERPNext REQUIREMENT)
		# --------------------------------------------------
		self.quotation.submit()

		# --------------------------------------------------
		# Quotation → Sales Order
		# --------------------------------------------------
		sales_order_name = frappe.call(
			"acuamania.acuamania.api.conversions.make_sales_order_and_insert",
			source_name=self.quotation.name,
		)

		self.sales_order = frappe.get_doc("Sales Order", sales_order_name)

		self.assertEqual(self.sales_order.quotation, self.quotation.name)
		self.assertTrue(self.sales_order.items)
		self.assertTrue(
			self.sales_order.delivery_date or any(row.delivery_date for row in self.sales_order.items)
		)
