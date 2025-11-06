import json
import frappe

DOCTYPE = "Customer Category"
FILE_PATH = frappe.get_app_path("acuamania", "nomenclators", "customer_categories.json")


def load_nomenclator(file_path):
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def record_exists(doctype, category_name):
    return frappe.db.exists(doctype, {"customer_category": category_name})


def create_record(entry):
    doc = frappe.new_doc(DOCTYPE)
    doc.customer_category = entry.get("customer_category")
    doc.save(ignore_permissions=True)


def execute():
    try:
        nomenclator = load_nomenclator(FILE_PATH)

        for entry in nomenclator:
            if not record_exists(DOCTYPE, entry["customer_category"]):
                create_record(entry)

        frappe.db.commit()
        frappe.logger().info(f"✅ Nomenclator '{DOCTYPE}' loaded successfully with {len(nomenclator)} records.")
    except Exception as e:
        frappe.log_error(message=str(e), title=f"{DOCTYPE} Sync Failed")
