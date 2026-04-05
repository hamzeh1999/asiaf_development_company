// For (shift Assignment) and (shift schedule assignment) and (Shift Assignment Tool) forms since they share the same logic around shift_location
window.ShiftUtils = {
    // =====================================================
    // 1️⃣ Setup – Filter shift_location based on project
    // =====================================================
    setup_location_query(frm) {
        frm._project_shift_locations = [];

        frm.set_query('shift_location', function () {
            let allowed = frm._project_shift_locations.slice();
            if (frm.doc.shift_location && !allowed.includes(frm.doc.shift_location)) {
                allowed.push(frm.doc.shift_location);
            }
            return {
                filters: { name: ['in', allowed.length ? allowed : ['']] }
            };
        });
    },

    // =====================================================
    // 2️⃣ UX – Enable/disable shift_location
    // =====================================================
    toggle_shift_location(frm) {
        const enabled = !!frm.doc.custom_project;
        frm.set_df_property('shift_location', 'read_only', !enabled);
    },

    // =====================================================
    // 3️⃣ Load locations from selected project
    // =====================================================
    load_project_locations(frm) {
        frm._project_shift_locations = [];
        ShiftUtils.toggle_shift_location(frm);

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
            },
            error() {
                frappe.msgprint({
                    title: __('Error'),
                    message: __('Could not load locations for this project.'),
                    indicator: 'red'
                });
            }
        });
    },

    // =====================================================
    // 4️⃣ Fetch Administrative Region & City from Shift Location
    // =====================================================
    fetch_location_details(frm) {
        if (!frm.doc.shift_location) return;

        frappe.db.get_value('Shift Location', frm.doc.shift_location,
            ['custom_administrative_region', 'custom_city'])
            .then(r => {
                const val = r.message;
                if (!val) return;

                const admin_id = val.custom_administrative_region || null;
                const city_id  = val.custom_city || null;

                const meta = frappe.get_meta(frm.doctype);
                const is_link = (fieldname) => {
                    const f = meta && meta.fields.find(f => f.fieldname === fieldname);
                    return f && f.fieldtype === 'Link';
                };
                const admin_is_link = is_link('custom_administrative_region');
                const city_is_link  = is_link('custom_city');

                const p_admin = admin_id
                    ? frappe.db.get_value('Administrative Region', admin_id, 'administrative_region')
                        .then(res => (res.message && res.message.administrative_region) || admin_id)
                        .catch(() => admin_id)
                    : Promise.resolve(null);

                const p_city = city_id
                    ? frappe.db.get_value('City', city_id, 'city')
                        .then(res => (res.message && res.message.city) || city_id)
                        .catch(() => city_id)
                    : Promise.resolve(null);

                Promise.all([p_admin, p_city]).then(([admin_title, city_title]) => {
                    if (admin_id) {
                        if (admin_is_link) {
                            frappe.utils.add_link_title('Administrative Region', admin_id, admin_title || admin_id);
                            frm.set_value('custom_administrative_region', admin_id);
                        } else {
                            frm.set_value('custom_administrative_region', admin_title || admin_id);
                        }
                    } else {
                        frm.set_value('custom_administrative_region', null);
                    }

                    if (city_id) {
                        if (city_is_link) {
                            frappe.utils.add_link_title('City', city_id, city_title || city_id);
                            frm.set_value('custom_city', city_id);
                        } else {
                            frm.set_value('custom_city', city_title || city_id);
                        }
                    } else {
                        frm.set_value('custom_city', null);
                    }
                });
            })
            .catch(error => {
                console.error('Error fetching location details:', error);
            });
    }

};