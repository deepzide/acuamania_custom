import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today


def create_test_customer():
	customer = frappe.new_doc("Customer")
	customer.customer_name = f"Test Promo Customer {frappe.generate_hash(length=6)}"
	customer.customer_group = "All Customer Groups"
	customer.save(ignore_permissions=True)
	return customer.name


def create_document_with_item(doctype, item_code, qty, rate=None):
	customer_name = create_test_customer()

	doc = frappe.new_doc(doctype)
	doc.customer = customer_name

	if doctype == "Sales Order":
		doc.delivery_date = today()
		doc.transaction_date = today()

	item = doc.append("items", {})
	item.item_code = item_code
	item.qty = qty
	if rate is not None:
		item.rate = rate

	if doctype == "Sales Order":
		item.delivery_date = doc.delivery_date
		item.schedule_date = doc.delivery_date

	return doc


def add_promotion(doc, promo_name):
	doc.append(
		"custom_promotion_table",
		{
			"promotion": promo_name,
		},
	)


class TestPromoEngine(FrappeTestCase):
	def run_promo_test(self, doctype, promo_name, qty, rate, expected):
		doc = create_document_with_item(doctype, "ENTR-GRAL", qty=qty, rate=rate)
		add_promotion(doc, promo_name)

		doc.save()

		self.assertEqual(
			doc.discount_amount,
			expected,
			f"{doctype} promo '{promo_name}' failed",
		)

	def test_mixed_items_required_free(self):
		doc = create_document_with_item("Quotation", "ENTR-GRAL", qty=2, rate=910)

		child = doc.append("items", {})
		child.item_code = "ENTR-NIÑO"
		child.qty = 2
		child.rate = 610

		add_promotion(doc, "4x1")
		doc.save()

		self.assertEqual(doc.discount_amount, 610)

	def test_so_mixed_items_required_free(self):
		doc = create_document_with_item("Sales Order", "ENTR-GRAL", qty=2, rate=910)

		child = doc.append("items", {})
		child.item_code = "ENTR-NIÑO"
		child.qty = 2
		child.rate = 610
		child.delivery_date = doc.delivery_date
		child.schedule_date = doc.delivery_date

		add_promotion(doc, "4x1")
		doc.save()

		self.assertEqual(doc.discount_amount, 610)

	def ensure_required_x_free_promo(self, name, required, free):
		if frappe.db.exists("Park Promotion", name):
			return

		promo = frappe.get_doc(
			{
				"doctype": "Park Promotion",
				"promotion_name": name,
				"apply_type": "requeridos x gratuitos",
				"required": required,
				"free": free,
				"active": 1,
				"valid_from": "2000-01-01",
				"valid_upto": "2099-12-31",
			}
		)
		promo.insert(ignore_permissions=True)

	def test_requeridos_x_gratuitos_even(self):
		self.run_promo_test(
			"Quotation",
			"ONFI 2x1",
			qty=4,
			rate=910,
			expected=1820,
		)

	def test_requeridos_x_gratuitos_odd(self):
		self.run_promo_test(
			"Quotation",
			"ONFI 2x1",
			qty=3,
			rate=910,
			expected=910,
		)

	def test_fixed_price(self):
		expected = (910 - 610) * 2
		self.run_promo_test(
			"Quotation",
			"Reencuentro - Todos Somos Residentes",
			qty=2,
			rate=910,
			expected=expected,
		)

	def test_percentage_discount(self):
		self.run_promo_test(
			"Quotation",
			"Descuento 10%",
			qty=2,
			rate=1000,
			expected=200,
		)

	def test_discount_amount(self):
		self.run_promo_test(
			"Quotation",
			"Descuento Fijo 500 UYU",
			qty=2,
			rate=900,
			expected=500,
		)

	def test_no_promotion_selected(self):
		"""
		If no promotion is selected, discount_amount must be 0.
		Discounts are owned exclusively by the promotion engine.
		"""
		doc = create_document_with_item("Quotation", "ENTR-GRAL", qty=2, rate=900)
		doc.discount_amount = 123

		doc.save()

		self.assertEqual(doc.discount_amount, 0)

	def test_so_requeridos_x_gratuitos_even(self):
		self.run_promo_test(
			"Sales Order",
			"ONFI 2x1",
			qty=4,
			rate=910,
			expected=1820,
		)

	def test_so_requeridos_x_gratuitos_odd(self):
		self.run_promo_test(
			"Sales Order",
			"ONFI 2x1",
			qty=3,
			rate=910,
			expected=910,
		)

	def test_so_fixed_price(self):
		expected = (910 - 610) * 2
		self.run_promo_test(
			"Sales Order",
			"Reencuentro - Todos Somos Residentes",
			qty=2,
			rate=910,
			expected=expected,
		)

	def test_so_percentage_discount(self):
		self.run_promo_test(
			"Sales Order",
			"Descuento 10%",
			qty=2,
			rate=1000,
			expected=200,
		)

	def test_so_discount_amount(self):
		self.run_promo_test(
			"Sales Order",
			"Descuento Fijo 500 UYU",
			qty=2,
			rate=900,
			expected=500,
		)

	def test_so_no_promotion_selected(self):
		"""
		If no promotion is selected, discount_amount must be 0.
		Discounts are owned exclusively by the promotion engine.
		"""
		doc = create_document_with_item("Sales Order", "ENTR-GRAL", qty=2, rate=900)
		doc.discount_amount = 123

		doc.save()

		self.assertEqual(doc.discount_amount, 0)
