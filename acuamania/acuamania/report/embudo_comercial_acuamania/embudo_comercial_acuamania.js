frappe.query_reports["Embudo Comercial Acuamania"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("Desde"),
			fieldtype: "Date",
			default: frappe.datetime.add_days(frappe.datetime.get_today(), -30),
		},
		{
			fieldname: "to_date",
			label: __("Hasta"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "channel",
			label: __("Canal"),
			fieldtype: "Link",
			options: "Lead Source",
		},
		{
			fieldname: "customer_type",
			label: __("Tipo de Cliente"),
			fieldtype: "Select",
			options: "\nIndividual\nGrupo\nCorporativo\nRecurrente\nNuevo",
		},
	],
};
