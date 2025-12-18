import frappe
from frappe.tests.utils import FrappeTestCase


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

        self.lead = frappe.get_doc({
            "doctype": "Lead",
            "first_name": "Test",
            "last_name": "Conversion",
            "email_id": "conversion@test.com",
            "phone": "099999999",
            "company": self.company,
        }).insert(ignore_permissions=True)

    def tearDown(self):
        for doc in [
            self.sales_order,
            self.quotation,
            self.opportunity,
            self.lead,
        ]:
            if doc:
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

        opportunity_name = frappe.call(
            "acuamania.acuamania.api.conversions.make_opportunity_and_insert",
            source_name=self.lead.name,
        )

        self.opportunity = frappe.get_doc("Opportunity", opportunity_name)

        self.assertEqual(self.opportunity.opportunity_from, "Lead")
        self.assertEqual(self.opportunity.party_name, self.lead.name)

        quotation_name = frappe.call(
            "acuamania.acuamania.api.conversions.make_quotation_and_insert",
            source_name=self.opportunity.name,
        )

        self.quotation = frappe.get_doc("Quotation", quotation_name)

        self.assertEqual(self.quotation.opportunity, self.opportunity.name)

        self.sales_order = frappe.get_doc({
            "doctype": "Sales Order",
        })

        sales_order_name = frappe.call(
            "acuamania.acuamania.api.conversions.make_sales_order_and_insert",
            source_name=self.quotation.name,
        )

        self.sales_order = frappe.get_doc("Sales Order", sales_order_name)

        self.assertEqual(self.sales_order.quotation, self.quotation.name)
