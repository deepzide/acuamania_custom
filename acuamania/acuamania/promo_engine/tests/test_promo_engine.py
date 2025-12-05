import frappe
from frappe.utils import today
from frappe.tests.utils import FrappeTestCase


def create_test_customer():
    customer = frappe.new_doc("Customer")
    customer.customer_name = "Test Promo Customer"
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


class TestPromoEngine(FrappeTestCase):

    def run_promo_test(self, doctype, promo_name, qty, rate, expected):
        print(f"▶️ Running promo test for {doctype} using promo '{promo_name}'")

        doc = create_document_with_item(doctype, "ENTR-GRAL", qty=qty, rate=rate)
        doc.custom_promotion_name = promo_name

        doc.save()

        print(f"🔍 discount={doc.discount_amount}, expected={expected}")
        self.assertEqual(doc.discount_amount, expected)

        return doc.discount_amount

    # ------------------------------------------------------
    # 🆕 NEW TEST: combinar entradas y regalar la más barata
    # ------------------------------------------------------

    def test_mixed_items_required_free(self):
        """
        Promo: required=4, free=1
        Ítems: 2 ENTR-GRAL @ 910 + 2 ENTR-NIÑO @ 610
        Resultado esperado: se regala la entrada más barata → 610
        """

        doc = create_document_with_item("Quotation", "ENTR-GRAL", qty=2, rate=910)
        child = doc.append("items", {})
        child.item_code = "ENTR-NIÑO"
        child.qty = 2
        child.rate = 610

        doc.custom_promotion_name = "4x1"  # nombre de tu promo real
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

        doc.custom_promotion_name = "4x1"
        doc.save()

        self.assertEqual(doc.discount_amount, 610)

    # ------------------------------------------------------
    # TUS TESTS ORIGINALES (NO TOCADOS)
    # ------------------------------------------------------

    def test_requeridos_x_gratuitos_even(self):
        self.run_promo_test(
            "Quotation",
            "ONFI 2x1",
            qty=4,
            rate=910,
            expected=1820
        )

    def test_requeridos_x_gratuitos_odd(self):
        self.run_promo_test(
            "Quotation",
            "ONFI 2x1",
            qty=3,
            rate=910,
            expected=910
        )

    def test_fixed_price(self):
        expected = (910 - 610) * 2
        self.run_promo_test(
            "Quotation",
            "Reencuentro - Todos Somos Residentes",
            qty=2,
            rate=910,
            expected=expected
        )

    def test_percentage_discount(self):
        self.run_promo_test(
            "Quotation",
            "Descuento 10%",
            qty=2,
            rate=1000,
            expected=200
        )

    def test_discount_amount(self):
        self.run_promo_test(
            "Quotation",
            "Descuento Fijo 500 UYU",
            qty=2,
            rate=900,
            expected=500
        )

    def test_no_promotion_selected(self):
        doc = create_document_with_item("Quotation", "ENTR-GRAL", qty=2, rate=900)
        doc.discount_amount = 123
        doc.save()
        self.assertEqual(doc.discount_amount, 123)

    # ----------------------------------------
    # SALES ORDER – test suite original
    # ----------------------------------------

    def test_so_requeridos_x_gratuitos_even(self):
        self.run_promo_test(
            "Sales Order",
            "ONFI 2x1",
            qty=4,
            rate=910,
            expected=1820
        )

    def test_so_requeridos_x_gratuitos_odd(self):
        self.run_promo_test(
            "Sales Order",
            "ONFI 2x1",
            qty=3,
            rate=910,
            expected=910
        )

    def test_so_fixed_price(self):
        expected = (910 - 610) * 2
        self.run_promo_test(
            "Sales Order",
            "Reencuentro - Todos Somos Residentes",
            qty=2,
            rate=910,
            expected=expected
        )

    def test_so_percentage_discount(self):
        self.run_promo_test(
            "Sales Order",
            "Descuento 10%",
            qty=2,
            rate=1000,
            expected=200
        )

    def test_so_discount_amount(self):
        self.run_promo_test(
            "Sales Order",
            "Descuento Fijo 500 UYU",
            qty=2,
            rate=900,
            expected=500
        )

    def test_so_no_promotion_selected(self):
        doc = create_document_with_item("Sales Order", "ENTR-GRAL", qty=2, rate=900)
        doc.discount_amount = 123
        doc.save()
        self.assertEqual(doc.discount_amount, 123)
