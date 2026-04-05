frappe.ui.form.on('Shift Location', {

    onload(frm) {
        set_city_query(frm);
        toggle_city(frm);
    },

    refresh(frm) {
        toggle_city(frm);
    },

    custom_administrative_region(frm) {
        // Reset dependent field
        if (frm.doc.custom_city) {
            frm.set_value('custom_city', null);
        }

        set_city_query(frm);
        toggle_city(frm);
    }

});

// ===============================
// Reusable Functions
// ===============================

function set_city_query(frm) {
    frm.set_query('custom_city', () => {

        // Safety check
        if (!frm.doc.custom_administrative_region) {
            return {
                filters: {
                    name: ["=", ""]
                }
            };
        }

        return {
            filters: {
                administrative_region: frm.doc.custom_administrative_region
            }
        };
    });
}

function toggle_city(frm) {
    const has_region = !!frm.doc.custom_administrative_region;

    // Better UX: disable instead of just filter
    frm.set_df_property('custom_city', 'read_only', !has_region);
}