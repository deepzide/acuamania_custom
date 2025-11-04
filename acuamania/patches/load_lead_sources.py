import json
import frappe

DOCTYPE = "Lead Source"
FILE_PATH = frappe.get_app_path("acuamania", "nomenclators", "lead_sources.json")


def load_nomenclator(file_path):
    """Load Lead Source records from JSON."""
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def record_exists(doctype, source_name):
    """Check if a Lead Source with the same name already exists."""
    return frappe.db.exists(doctype, {"source_name": source_name})


def create_record(entry):
    """Create a new Lead Source record."""
    doc = frappe.new_doc(DOCTYPE)
    doc.source_name = entry.get("source_name")
    doc.save(ignore_permissions=True)


def execute():
    """Patch entry point."""
    try:
        nomenclator = load_nomenclator(FILE_PATH)

        for entry in nomenclator:
            if not record_exists(DOCTYPE, entry["source_name"]):
                create_record(entry)

        frappe.db.commit()
        frappe.logger().info(f"✅ Nomenclator '{DOCTYPE}' loaded successfully with {len(nomenclator)} records.")
    except Exception as e:
        frappe.log_error(message=str(e), title=f"{DOCTYPE} Sync Failed")
