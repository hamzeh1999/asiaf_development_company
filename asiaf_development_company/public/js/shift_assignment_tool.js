frappe.ui.form.on('Shift Assignment Tool', {

    setup(frm) {
        // Project-based location query — active for both Assign Shift and Assign Shift Schedule
        frm._project_shift_locations = [];
        frm._sat_location_query_set = false;
    },

    refresh(frm) {
        sat_toggle_custom_section(frm);

        if (sat_is_project_action(frm) && frm.doc.custom_project) {
            sat_load_project_locations(frm);
        }

        if (sat_is_project_action(frm) && frm.doc.shift_location && !frm.doc.custom_administrative_region) {
            ShiftUtils.fetch_location_details(frm);
        }
    },

    action(frm) {
        sat_toggle_custom_section(frm);
    },

    custom_project(frm) {
        // Reset dependent fields when project changes
        frm.set_value('shift_location', null);
        frm.set_value('custom_administrative_region', null);
        frm.set_value('custom_city', null);
        sat_load_project_locations(frm);
    },

    shift_location(frm) {
        if (!sat_is_project_action(frm)) return;

        if (frm.doc.shift_location) {
            ShiftUtils.fetch_location_details(frm);
        } else {
            frm.set_value('custom_administrative_region', null);
            frm.set_value('custom_city', null);
        }
    }

});

// ─── Helpers (local to this file) ───────────────────────────────

function sat_is_project_action(frm) {
    return frm.doc.action === 'Assign Shift' || frm.doc.action === 'Assign Shift Schedule';
}

function sat_toggle_custom_section(frm) {
    const is_project_action = sat_is_project_action(frm);

    // shift_location: always visible via section depends_on,
    // but read-only until a project supplies the allowed list
    frm.set_df_property('shift_location', 'read_only', is_project_action ? !frm.doc.custom_project : false);

    // Install / remove the project-based location filter
    if (is_project_action) {
        sat_install_location_query(frm);
    } else {
        sat_remove_location_query(frm);
    }
}

function sat_install_location_query(frm) {
    if (frm._sat_location_query_set) return;
    frm.set_query('shift_location', function () {
        const allowed = (frm._project_shift_locations || []).slice();
        if (frm.doc.shift_location && !allowed.includes(frm.doc.shift_location)) {
            allowed.push(frm.doc.shift_location);
        }
        return { filters: { name: ['in', allowed.length ? allowed : ['']] } };
    });
    frm._sat_location_query_set = true;
}

function sat_remove_location_query(frm) {
    if (!frm._sat_location_query_set) return;
    frm.set_query('shift_location', function () { return {}; });
    frm._sat_location_query_set = false;
}

function sat_load_project_locations(frm) {
    frm._project_shift_locations = [];
    sat_toggle_custom_section(frm);

    if (!frm.doc.custom_project) return;

    frappe.call({
        method: 'asiaf_development_company.asiaf_development_company.project.api.get_project_shift_locations',
        args: { project: frm.doc.custom_project },
        callback(r) {
            frm._project_shift_locations = (r.message || []).filter(Boolean);
            if (frm.doc.shift_location && !frm._project_shift_locations.includes(frm.doc.shift_location)) {
                frm.set_value('shift_location', null);
            }
            frm.refresh_field('shift_location');
            frm.set_df_property('shift_location', 'read_only', false);
        },
        error() {
            frappe.msgprint({
                title: __('Error'),
                message: __('Could not load locations for this project.'),
                indicator: 'red'
            });
        }
    });
}
