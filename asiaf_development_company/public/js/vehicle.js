frappe.ui.form.on('Vehicle', {
    setup(frm) {
        frm.set_query('custom_asset_reference', function() {
            return {
                filters: {
                    asset_category: 'Vehicles'
                }
            };
        });
    }
});