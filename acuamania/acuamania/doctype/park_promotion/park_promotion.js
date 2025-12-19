// Copyright (c) 2025, cegomezpy and contributors
// For license information, please see license.txt

frappe.ui.form.on("Park Promotion", {
	refresh(frm) {
		frm.trigger("apply_type");
	},

	apply_type(frm) {
		update_fields_by_apply_type(frm);
	},
});

function update_fields_by_apply_type(frm) {
	reset_promo_fields(frm);

	const applyType = frm.doc.apply_type;

	if (!applyType) {
		return;
	}

	if (applyType === "requeridos x gratuitos") {
		set_required_x_free_rules(frm);
		return;
	}

	if (applyType === "porcentaje") {
		set_percentage_rules(frm);
		return;
	}

	if (applyType === "precio fijo") {
		set_fixed_price_rules(frm);
		return;
	}

	if (applyType === "precio de descuento") {
		set_discount_amount_rules(frm);
		return;
	}
}

function reset_promo_fields(frm) {
	const fields = ["required", "free", "discount_percentage", "fixed_price", "discount_amount"];

	fields.forEach((fieldname) => {
		frm.toggle_display(fieldname, false);
		frm.set_df_property(fieldname, "reqd", false);
	});
}

function set_required_x_free_rules(frm) {
	frm.toggle_display(["required", "free"], true);

	frm.set_df_property("required", "reqd", true);
	frm.set_df_property("free", "reqd", true);
}

function set_percentage_rules(frm) {
	frm.toggle_display("discount_percentage", true);
	frm.set_df_property("discount_percentage", "reqd", true);
}

function set_fixed_price_rules(frm) {
	frm.toggle_display("fixed_price", true);
	frm.set_df_property("fixed_price", "reqd", true);
}

function set_discount_amount_rules(frm) {
	frm.toggle_display("discount_amount", true);
	frm.set_df_property("discount_amount", "reqd", true);
}
