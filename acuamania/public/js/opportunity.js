frappe.ui.form.on('Opportunity Item', {
    item_code: function (frm, cdt, cdn) {
        const row = frappe.get_doc(cdt, cdn);

        if (!row.item_code) {
            return;
        }

        fetch_item_rate_and_update_row(frm, cdt, cdn);
    },

    qty: function (frm, cdt, cdn) {
        const row = frappe.get_doc(cdt, cdn);

        if (!row.rate || !row.qty) {
            return;
        }

        const amount = flt(row.rate) * flt(row.qty);
        frappe.model.set_value(cdt, cdn, 'amount', amount);
    }
});

function fetch_item_rate_and_update_row(frm, cdt, cdn) {
    const row = frappe.get_doc(cdt, cdn);

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Item Price',
            filters: {
                item_code: row.item_code,
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
            const amount = rate * qty;

            frappe.model.set_value(cdt, cdn, {
                rate: rate,
                amount: amount
            });
        }
    });
}
