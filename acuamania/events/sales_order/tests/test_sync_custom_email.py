import logging
import os
import sys

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today


class TestSalesOrderSyncCustomEmail(FrappeTestCase):
	"""Validate that Sales Order.custom_email automatically syncs to contact_email on before_save."""

	@classmethod
	def setUpClass(cls):
		"""Initialize logger (stdout + file) and ensure test dependencies."""
		log_dir = frappe.get_site_path("logs")
		os.makedirs(log_dir, exist_ok=True)
		log_path = os.path.join(log_dir, "test_sales_order_sync_custom_email.log")

		cls.logger = logging.getLogger("test_sales_order_sync_custom_email")
		cls.logger.setLevel(logging.INFO)

		console_handler = logging.StreamHandler(sys.stdout)
		console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
		file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
		file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

		cls.logger.addHandler(console_handler)
		cls.logger.addHandler(file_handler)
		cls.logger.propagate = False

		cls.logger.info("🧪 Starting TestSalesOrderSyncCustomEmail suite...")
		cls.logger.info(f"📂 Log file: {log_path}")

		# --- Ensure test dependencies exist and are committed ---
		if not frappe.db.exists("Customer", {"customer_name": "Test Email Customer"}):
			frappe.get_doc({"doctype": "Customer", "customer_name": "Test Email Customer"}).insert(
				ignore_permissions=True
			)
			cls.logger.info("✅ Created test Customer.")
			frappe.db.commit()  # <-- ensure it's visible to subsequent transactions

		if not frappe.db.exists("Item", {"item_code": "Test Email Item"}):
			frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": "Test Email Item",
					"item_name": "Test Email Item",
					"is_stock_item": 0,
					"item_group": "All Item Groups",
				}
			).insert(ignore_permissions=True)
			cls.logger.info("✅ Created test Item.")
			frappe.db.commit()

	def setUp(self):
		frappe.db.rollback()
		self.logger.info("🔧 Setting up new Sales Order...")

	def tearDown(self):
		"""Safely delete created Sales Orders."""
		self.logger.info("🧹 Cleaning up test data...")
		for name in frappe.get_all("Sales Order", filters={"customer": "Test Email Customer"}, pluck="name"):
			frappe.delete_doc("Sales Order", name, force=True, ignore_permissions=True)
		frappe.db.commit()
		self.logger.info("✅ Cleanup completed.")

	def test_sales_order_custom_email_syncs_to_contact_email(self):
		"""Ensure before_save hook updates contact_email from custom_email."""
		self.logger.info("🚀 Running Sales Order email sync test...")

		# Create Sales Order — before_save hook should trigger automatically
		so = frappe.get_doc(
			{
				"doctype": "Sales Order",
				"customer": "Test Email Customer",
				"transaction_date": today(),
				"custom_email": "so_test@example.com",
				"contact_email": "",
				"items": [{"item_code": "Test Email Item", "qty": 1, "rate": 100, "delivery_date": today()}],
			}
		).insert(ignore_permissions=True)

		self.logger.info(f"✅ Sales Order inserted: {so.name}")
		self.logger.info(f"🔍 Values → custom_email={so.custom_email}, contact_email={so.contact_email}")

		# Reload to confirm persisted state
		so.reload()

		self.assertEqual(
			so.contact_email,
			"so_test@example.com",
			"contact_email should automatically sync from custom_email on save.",
		)

		self.logger.info("✅ Hook executed successfully and contact_email was updated.")
