import frappe


def with_sync_guard(func):
	def wrapper(*args, **kwargs):
		if getattr(frappe.flags, "sync_in_progress", False):
			return
		frappe.flags.sync_in_progress = True
		try:
			return func(*args, **kwargs)
		finally:
			frappe.flags.sync_in_progress = False

	return wrapper
