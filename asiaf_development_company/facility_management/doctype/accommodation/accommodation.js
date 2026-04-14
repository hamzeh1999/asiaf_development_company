frappe.ui.form.on('Accommodation', {
    setup(frm) {
        frm.set_query('asiaf_buildings', function() {
            return {
                filters: {
                    asset_category: 'Buildings'
                }
            };
        });
    },

    ownership_type(frm) {
        if (frm.doc.ownership_type !== 'Owned') {
            frm.set_value('asiaf_buildings', '');
        }
    }
});