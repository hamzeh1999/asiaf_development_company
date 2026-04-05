frappe.ui.form.on('Project Site', {

    setup(frm) {
        frm.set_query("city", function() {
            if (frm.doc.administrative_region) {
                return {
                    filters: {
                        administrative_region: frm.doc.administrative_region
                    }
                };
            }
        });
    },

    latitude(frm) {
        update_location(frm);
    },

    longitude(frm) {
        update_location(frm);
    }
});

function update_location(frm) {

    if (frm.doc.latitude && frm.doc.longitude) {

        let geojson = {
            "type": "Point",
            "coordinates": [
                parseFloat(frm.doc.longitude), 
                parseFloat(frm.doc.latitude)
            ]
        };

        frm.doc.site_location = JSON.stringify(geojson);
        frm.refresh_field("site_location");
    }
}