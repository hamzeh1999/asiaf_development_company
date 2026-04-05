frappe.ui.form.on('Shift Schedule Assignment', {

    setup(frm) {
        ShiftUtils.setup_location_query(frm);
    },

    onload(frm) {
        ShiftUtils.toggle_shift_location(frm);
        if (frm.doc.custom_project) frm.trigger('custom_project');
    },

    refresh(frm) {
        ShiftUtils.toggle_shift_location(frm);

        // Reload project locations on every refresh so the filter is never stale
        if (frm.doc.custom_project) {
            ShiftUtils.load_project_locations(frm);
        }

        if (!frm.is_new() && frm.doc.shift_location && !frm.doc.custom_administrative_region) {
            ShiftUtils.fetch_location_details(frm);
        }
    },

    custom_project(frm) {
        ShiftUtils.load_project_locations(frm);
    },

    shift_location(frm)  { ShiftUtils.fetch_location_details(frm); },

    validate(frm) {
    }

});