import unittest

import frappe

from acuamania.patches import hide_lead_mobile_no as patch

LEAD_DOCTYPE = "Lead"
FIELDNAME = "mobile_no"


class TestHideMobileNoInLead(unittest.TestCase):
	def setUp(self):
		frappe.db.rollback()
		self.docfield_name = frappe.db.exists("DocField", {"parent": LEAD_DOCTYPE, "fieldname": FIELDNAME})
		if self.docfield_name:
			docfield = frappe.get_doc("DocField", self.docfield_name)
			docfield.hidden = 0
			docfield.save(ignore_permissions=True)
			frappe.db.commit()

	def tearDown(self):
		frappe.db.rollback()

	def test_patch_hides_mobile_no_field(self):
		patch.execute()
		docfield_name = frappe.db.exists("DocField", {"parent": LEAD_DOCTYPE, "fieldname": FIELDNAME})
		self.assertTrue(docfield_name)
		docfield = frappe.get_doc("DocField", docfield_name)
		self.assertEqual(docfield.hidden, 1)
