import frappe
from frappe.tests.utils import FrappeTestCase


def create_test_customer():
    """Create a minimal customer for use in promo tests."""
    print("🔧 Creating test customer")

    customer = frappe.new_doc("Customer")
    customer.customer_name = "Test Promo Customer"
    customer.customer_group = "All Customer Groups"
    customer.save(ignore_permissions=True)

    print(f"✅ Customer created: {customer.name}")
    return customer.name


def create_quotation_with_item(item_code, qty, rate=None):
    """Create a new (not yet inserted) Quotation with a single item."""
    customer_name = create_test_customer()

    print(f"🧾 Creating quotation draft: item={item_code}, qty={qty}, rate={rate}")

    quotation = frappe.new_doc("Quotation")
    quotation.customer = customer_name

    item = quotation.append("items", {})
    item.item_code = item_code
    item.qty = qty
    if rate is not None:
        item.rate = rate

    return quotation


class TestPromoEngine(FrappeTestCase):
    """
    Tests for the Acuamania Promotion Engine.

    These tests rely on the hook:
        Quotation.before_save → apply_selected_promotion
    """

    def test_two_for_one_even(self):
        print("▶️ test_two_for_one_even starting")

        quotation = create_quotation_with_item("ENTR-GRAL", qty=4, rate=910)
        quotation.custom_selected_promotion = "PROMO-ONFI-2X1"

        quotation.insert()

        print(f"🔍 discount={quotation.discount_amount}")
        self.assertEqual(quotation.discount_amount, 1820)

    def test_two_for_one_odd(self):
        print("▶️ test_two_for_one_odd starting")

        quotation = create_quotation_with_item("ENTR-GRAL", qty=3, rate=910)
        quotation.custom_selected_promotion = "PROMO-ONFI-2X1"

        quotation.insert()

        print(f"🔍 discount={quotation.discount_amount}")
        self.assertEqual(quotation.discount_amount, 910)

    def test_fixed_price(self):
        print("▶️ test_fixed_price starting")

        quotation = create_quotation_with_item("ENTR-GRAL", qty=2, rate=910)
        quotation.custom_selected_promotion = "PROMO-REENC-RESIDENTES"

        quotation.insert()

        expected = (910 - 610) * 2
        print(f"🔍 discount={quotation.discount_amount}, expected={expected}")

        self.assertEqual(quotation.discount_amount, expected)

    def test_percentage_discount(self):
        print("▶️ test_percentage_discount starting")

        quotation = create_quotation_with_item("ENTR-GRAL", qty=2, rate=1000)
        quotation.custom_selected_promotion = "PROMO-PCT-10"

        quotation.insert()

        print(f"🔍 discount={quotation.discount_amount}")
        self.assertEqual(quotation.discount_amount, 200)

    def test_discount_amount(self):
        print("▶️ test_discount_amount starting")

        quotation = create_quotation_with_item("ENTR-GRAL", qty=2, rate=900)
        quotation.custom_selected_promotion = "PROMO-FLAT-500"

        quotation.insert()

        print(f"🔍 discount={quotation.discount_amount}")
        self.assertEqual(quotation.discount_amount, 500)

    def test_no_promotion_selected(self):
        print("▶️ test_no_promotion_selected starting")

        quotation = create_quotation_with_item("ENTR-GRAL", qty=2, rate=900)
        quotation.discount_amount = 123  # simulate existing discount

        quotation.insert()

        print(f"🔍 discount after insert={quotation.discount_amount}")
        self.assertEqual(quotation.discount_amount, 123)
