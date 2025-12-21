import frappe
from frappe.utils import flt, nowdate

DEPOSIT_PERCENTAGE = 0.50


def create_two_payment_entries(invoice):
    frappe.msgprint(f"[AUTO-PE] Processing Sales Invoice {invoice.name}")

    outstanding = flt(invoice.outstanding_amount)

    if outstanding <= 0:
        frappe.msgprint("[AUTO-PE] No outstanding amount, skipping")
        return

    if _has_existing_payments(invoice):
        frappe.msgprint("[AUTO-PE] Existing Payment Entries found, aborting")
        return

    mode_of_payment = _resolve_mode_of_payment(invoice.company)

    if not mode_of_payment:
        frappe.throw("No Mode of Payment configured for this company.")

    amounts = _calculate_split_amounts(outstanding)

    _create_payment_entry(
        invoice,
        {
            "payment_type": "Receive",
            "mode_of_payment": mode_of_payment,
            "allocated_amount": amounts["deposit"],
            "title": "AUTO - Deposit 50%",
        },
    )

    _create_payment_entry(
        invoice,
        {
            "payment_type": "Receive",
            "mode_of_payment": mode_of_payment,
            "allocated_amount": amounts["balance"],
            "title": "AUTO - Balance 50%",
        },
    )

    frappe.msgprint("[AUTO-PE] Payment Entries created successfully")


def _has_existing_payments(invoice):
    exists = frappe.db.exists(
        "Payment Entry Reference",
        {
            "reference_doctype": "Sales Invoice",
            "reference_name": invoice.name,
        },
    )
    frappe.msgprint(f"[AUTO-PE] Existing payments: {bool(exists)}")
    return bool(exists)


def _resolve_mode_of_payment(company):
    rows = frappe.get_all(
        "Mode of Payment Account",
        filters={"company": company},
        fields=["parent"],
        order_by="modified desc",
        limit=1,
    )
    return rows[0].parent if rows else None


def _calculate_split_amounts(outstanding):
    deposit = flt(outstanding * DEPOSIT_PERCENTAGE)
    balance = flt(outstanding - deposit)
    frappe.msgprint(
        f"[AUTO-PE] Split calculated → deposit={deposit}, balance={balance}"
    )
    return {
        "deposit": deposit,
        "balance": balance,
    }


def _create_payment_entry(invoice, params):
    """
    params = {
        payment_type: "Receive" | "Pay",
        mode_of_payment: str,
        allocated_amount: float,
        title: str,
    }
    """

    frappe.msgprint(
        f"[AUTO-PE] Creating Payment Entry '{params['title']}' "
        f"type={params['payment_type']} amount={params['allocated_amount']}"
    )

    pe_payload = frappe.call(
        "erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry",
        dt="Sales Invoice",
        dn=invoice.name,
    )

    payment_entry = frappe.get_doc(pe_payload)

    payment_entry.payment_type = params["payment_type"]
    payment_entry.posting_date = invoice.posting_date or nowdate()
    payment_entry.mode_of_payment = params["mode_of_payment"]

    if not payment_entry.get("references"):
        frappe.throw("[AUTO-PE] No references generated in Payment Entry")

    payment_entry.references[0].allocated_amount = flt(
        params["allocated_amount"]
    )

    payment_entry.paid_amount = flt(params["allocated_amount"])
    payment_entry.received_amount = flt(params["allocated_amount"])

    if not payment_entry.source_exchange_rate:
        payment_entry.source_exchange_rate = 1.0

    if not payment_entry.target_exchange_rate:
        payment_entry.target_exchange_rate = 1.0

    payment_entry.remarks = params["title"]

    payment_entry.insert(ignore_permissions=True)

    frappe.msgprint(
        f"[AUTO-PE] Payment Entry {payment_entry.name} created (Draft)"
    )
