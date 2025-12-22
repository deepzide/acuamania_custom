frappe.ui.form.on('Opportunity Item', {
    item_code: function (frm, cdt, cdn) {
        const row = frappe.get_doc(cdt, cdn);

        if (!row.item_code) {
            return;
        }

        fetch_price_from_item_price(frm, cdt, cdn);
    },

    qty: function (frm, cdt, cdn) {
        const row = frappe.get_doc(cdt, cdn);
        if (!row.rate || !row.qty) return;

        frappe.model.set_value(
            cdt,
            cdn,
            'amount',
            flt(row.rate) * flt(row.qty)
        );
    }
});

function fetch_price_from_item_price(frm, cdt, cdn) {
    const row = frappe.get_doc(cdt, cdn);

    const price_list =
        frm.doc.selling_price_list ||
        frappe.defaults.get_default('selling_price_list');

    if (!price_list) {
        return;
    }

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Item Price',
            filters: {
                item_code: row.item_code,
                price_list: price_list,
                selling: 1
            },
            fieldname: ['price_list_rate']
        },
        callback: function (r) {
            if (!r.message || !r.message.price_list_rate) {
                return;
            }

            const rate = flt(r.message.price_list_rate);
            const qty = flt(row.qty) || 1;

            frappe.model.set_value(cdt, cdn, {
                rate: rate,
                amount: rate * qty
            });
        }
    });
}
