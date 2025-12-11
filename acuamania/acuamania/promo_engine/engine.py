import frappe
from frappe.utils import today
from acuamania.acuamania.promo_engine.rules import (
    apply_required_x_free,
    apply_fixed_price,
    apply_percentage_discount,
    apply_discount_amount,
)


def apply_selected_promotion(doc, method=None):
    """
    Hook para Quotation (validate o before_save).
    """

    frappe.msgprint("🔵 DEBUG: Entrando a apply_selected_promotion()")

    promo_name = getattr(doc, "custom_promotion_name", None)
    combo_promo_name = getattr(doc, "custom_combo_promotion_name", None)
    frappe.msgprint(f"🔵 DEBUG: Promoción seleccionada = {promo_name}")

    if not promo_name and not combo_promo_name:
        frappe.msgprint("🟡 DEBUG: No hay promoción seleccionada → No se aplica")
        return

    # --- 1) Cargar promoción ---
    try:
        frappe.msgprint(f"🔵 DEBUG: Cargando Park Promotion '{promo_name}'")
        promo = frappe.get_doc("Park Promotion", promo_name)
        frappe.msgprint(f"🟢 DEBUG: Promoción cargada con éxito → {promo.promotion_name}")
    except frappe.DoesNotExistError:
        frappe.msgprint("🔴 ERROR: La promoción seleccionada NO existe en el sistema")
        return

    # --- 2) Agrupar ítems ---
    frappe.msgprint("🔵 DEBUG: Agrupando ítems por código...")
    items_by_code = group_items_by_code(doc)

    if not items_by_code:
        frappe.msgprint("🔴 ERROR: No hay ítems para aplicar promoción")
        return

    frappe.msgprint(f"🟢 DEBUG: Ítems agrupados → {list(items_by_code.keys())}")

    # --- 3) Ejecutar lógica específica de la promoción ---
    frappe.msgprint("🔵 DEBUG: Calculando descuento con dispatch_promotion_logic()...")
    discount = dispatch_promotion_logic(promo, items_by_code)

    frappe.msgprint(f"🟣 DEBUG: Resultado del descuento calculado = {discount}")

    # --- 4) Si no hay descuento ---
    if not discount or discount <= 0:
        frappe.msgprint("🟡 DEBUG: El descuento calculado es 0 o inválido → limpiar promoción")
        if hasattr(doc, "custom_promotion_name"):
            doc.custom_promotion_name = ""
        doc.apply_discount_on = "Grand Total"
        doc.additional_discount_percentage = 0
        doc.discount_amount = 0
        return

    # --- 5) Aplicar descuento al documento ---
    frappe.msgprint(f"🟢 DEBUG: Aplicando descuento final = {discount}")
    apply_document_discount(doc, discount)

    # --- 6) Anotar la promoción ---
    frappe.msgprint("🔵 DEBUG: Guardando nombre de promoción en Promo Seleccionada")
    set_promotion_annotation(doc, promo)

    frappe.msgprint("✅ DEBUG: Promoción aplicada correctamente")


def group_items_by_code(doc):
    """
    Agrupa los ítems del documento por item_code.
    """
    frappe.msgprint("🔵 DEBUG: Entrando a group_items_by_code()")

    grouped = {}
    for row in getattr(doc, "items", []):
        if row.item_code:
            grouped.setdefault(row.item_code, []).append(row)

    frappe.msgprint(f"🟢 DEBUG: Ítems detectados → {list(grouped.keys())}")

    return grouped


def dispatch_promotion_logic(promo, items_by_code):
    frappe.msgprint(f"🔵 DEBUG: Entrando a dispatch_promotion_logic() con tipo={promo.apply_type}")

    promo_type = promo.apply_type

    if promo_type == "requeridos x gratuitos":
        frappe.msgprint("🟣 DEBUG: Ejecutando regla requeridos_x_gratuitos")
        return apply_required_x_free(promo, items_by_code)

    if promo_type == "precio fijo":
        frappe.msgprint("🟣 DEBUG: Ejecutando regla fixed_price")
        return apply_fixed_price(promo, items_by_code)

    if promo_type == "porcentaje":
        frappe.msgprint("🟣 DEBUG: Ejecutando regla percentage")
        return apply_percentage_discount(promo, items_by_code)

    if promo_type == "precio de descuento":
        frappe.msgprint("🟣 DEBUG: Ejecutando regla discount_amount")
        return apply_discount_amount(promo, items_by_code)

    frappe.msgprint("🔴 ERROR: Tipo de promoción DESCONOCIDO, devolviendo 0")
    return 0


def get_applicable_promotions(doc):
    """
    Lista promociones activas y vigentes. No se modifica.
    """
    doc_date = (
        getattr(doc, "transaction_date", None)
        or getattr(doc, "posting_date", None)
        or today()
    )

    return frappe.get_all(
        "Park Promotion",
        filters={
            "active": 1,
            "valid_from": ["<=", doc_date],
            "valid_upto": [">=", doc_date],
        },
        fields=["name", "promotion_name", "apply_type"],
        order_by="valid_from asc, promotion_name asc",
    )


def apply_document_discount(doc, discount_amount):
    """
    Aplica descuento a nivel Grand Total y fuerza recalculación para que ERPNext
    no sobreescriba el valor en el primer save.
    """

    doc.apply_discount_on = "Grand Total"
    doc.additional_discount_percentage = 0
    doc.discount_amount = discount_amount

    # 🚀 Force ERPNext to recalculate totals NOW
    try:
        doc.run_method("apply_discount")
    except Exception:
        pass

    try:
        doc.run_method("calculate_taxes_and_totals")
    except Exception:
        pass



def set_promotion_annotation(doc, promo):
    """
    Guarda el nombre de la promo aplicada.
    """
    frappe.msgprint(f"🔵 DEBUG: set_promotion_annotation() con promo={promo.promotion_name}")

    if hasattr(doc, "custom_promotion_name"):
        doc.custom_selected_promotion = promo.promotion_name or promo.name
        frappe.msgprint(f"🟢 DEBUG: custom_promotion_name → {doc.custom_promotion_name}")
