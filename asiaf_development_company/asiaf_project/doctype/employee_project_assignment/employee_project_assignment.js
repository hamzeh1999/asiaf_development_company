frappe.ui.form.on("Employee Project Assignment", {

    // =====================================================
    // SETUP & LIVE FILTERING
    // =====================================================
    setup: function(frm) {
        frm._project_sites = [];

        // 1. Filter sites based on project
        frm.set_query("custom_site", function() {
            if (!frm._project_sites || !frm._project_sites.length) {
                return { filters: { name: ["in", [""]] } };
            }
            return { filters: { name: ["in", frm._project_sites] } };
        });

        // 2. REFRESH FILTER ON CLICK (This fixes the "Still Visible" problem)
        frm.set_query("employee", "employee_table", function(doc, cdt, cdn) {
            const selected = (doc.employee_table || []).map(r => r.employee).filter(Boolean);
            
            let filters = [
                ["status", "=", "Active"],
                ["name", "not in", selected]
            ];

            // This line ensures that ONLY employees matching the current Job Title are visible
            if (doc.job_title) {
                filters.push(["custom_iqama_job_title", "=", doc.job_title]);
            } else {
                // If no job title is selected, show NO employees
                filters.push(["name", "=", "NOT_FOUND"]);
            }

            return { filters: filters };
        });
    },

    onload: function(frm) {
        frm.set_df_property("custom_site", "hidden", 0);
        if (frm.fields_dict.custom_site) {
            frm.fields_dict.custom_site.$wrapper.find('input, .link-btn').prop('disabled', true);
        }
        if (frm.doc.custom_project) {
            frm.trigger("custom_project");
        }
    },

    // =====================================================
    // PROJECT CHANGE (Site Filtering)
    // =====================================================
    custom_project: function(frm) {
        if (!frm.fields_dict.custom_site) return;
        const site_input = frm.fields_dict.custom_site.$wrapper.find('input, .link-btn');
        if (!frm.doc.custom_project) {
            frm.set_value("custom_site", null);
            site_input.prop('disabled', true);
            return;
        }
        site_input.prop('disabled', false);

        Promise.all([
            frappe.db.get_doc("Project", frm.doc.custom_project),
            frappe.db.get_list("Employee Project Assignment", {
                filters: {
                    custom_project: frm.doc.custom_project,
                    name: ["!=", frm.doc.name],
                    docstatus: ["!=", 2]
                },
                fields: ["custom_site"]
            })
        ]).then(([project, used_records]) => {
            const all_sites = (project.custom_site || []).map(row => row.site).filter(Boolean);
            const saved_sites = used_records.map(r => r.custom_site).filter(Boolean);
            frm._project_sites = all_sites.filter(site => !saved_sites.includes(site));
            frm.refresh_field("custom_site");
        });
    },

    // =====================================================
    // ADD EMPLOYEES BUTTON
    // =====================================================
    add_employee_button: function(frm) {
        if (frm.__adding_employees) return;
        if (!frm.doc.job_title) {
            frappe.msgprint(__('Please select a Job Title first'));
            return;
        }

        const limit = frm.doc.quantity || 0;
        frm.__adding_employees = true;

        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Employee",
                fields: ["name", "employee_name", "custom_iqama_job_title", "first_name", "middle_name", "last_name"],
                filters: { 
                    custom_iqama_job_title: frm.doc.job_title,
                    status: "Active" 
                },
                limit_page_length: limit
            },
            freeze: true,
            callback: async function(r) {
                const employees = r.message || [];
                if (!employees.length) {
                    frappe.msgprint(__('No Active employees found for this Job Title'));
                    frm.__adding_employees = false;
                    return;
                }

                let added_count = 0;
                let skipped_count = 0;

                let current_table = frm.doc.employee_table || [];
                if (current_table.length === 1 && !current_table[0].employee) {
                    frm.clear_table("employee_table");
                }

                const existing_in_table = (frm.doc.employee_table || []).map(r => r.employee);
                
                for (let emp of employees) {
                    if (!existing_in_table.includes(emp.name)) {
                        let is_already_assigned = await check_existing_assignment(frm, emp.name, true);
                        if (!is_already_assigned) {
                            const row = frm.add_child("employee_table");
                            const fullName = [emp.first_name, emp.middle_name, emp.last_name].filter(Boolean).join(' ');
                            
                            frappe.model.set_value(row.doctype, row.name, {
                                "employee": emp.name,
                                "employee_name": emp.employee_name ? emp.employee_name.split(':').pop().trim() : '',
                                "iqama_job_title": emp.custom_iqama_job_title || '',
                                "full_name": fullName
                            });
                            added_count++;
                        } else {
                            skipped_count++;
                        }
                    }
                }

                frm.refresh_field("employee_table");
                update_quantity(frm); 
                
                if (skipped_count > 0) {
                    frappe.show_alert({
                        message: __("Added {0}. {1} skipped (already assigned).", [added_count, skipped_count]),
                        indicator: 'orange'
                    });
                }
                frm.__adding_employees = false;
            }
        });
    }
});

// =====================================================
// CHILD TABLE EVENTS
// =====================================================
frappe.ui.form.on('Project Employee Assignment Item', {
    
    employee: async function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.employee) {
            frappe.model.set_value(cdt, cdn, {"employee_name": '', "iqama_job_title": '', "full_name": ''});
            update_quantity(frm);
            return;
        }

        let already_assigned = await check_existing_assignment(frm, row.employee, false);
        if (already_assigned) {
            frappe.model.set_value(cdt, cdn, "employee", "");
            return;
        }

        frappe.db.get_value('Employee', row.employee, ['employee_name', 'custom_iqama_job_title', 'first_name', 'middle_name', 'last_name'])
        .then(r => {
            const emp = r.message;
            if (emp) {
                const fullName = [emp.first_name, emp.middle_name, emp.last_name].filter(Boolean).join(' ');
                frappe.model.set_value(cdt, cdn, {
                    "employee_name": emp.employee_name ? emp.employee_name.split(':').pop().trim() : '',
                    "iqama_job_title": emp.custom_iqama_job_title || '',
                    "full_name": fullName
                });
                update_quantity(frm);
            }
        });
    },

    employee_table_add: function(frm) { update_quantity(frm); },
    employee_table_remove: function(frm) { update_quantity(frm); }
});

// =====================================================
// HELPER: CONFLICT CHECKER 
// =====================================================
async function check_existing_assignment(frm, employee_id, silent = false) {
    const child_doctype = "Project Employee Assignment Item"; 

    try {
        let result = await frappe.db.get_list(child_doctype, {
            filters: {
                employee: employee_id,
                parent: ["!=", frm.doc.name], 
                docstatus: ["!=", 2]          
            },
            fields: ['parent']
        });

        if (result && result.length > 0) {
            if (!silent) {
                let parent_data = await frappe.db.get_value('Employee Project Assignment', result[0].parent, ['custom_project', 'custom_site']);

                let project_name = parent_data.message.custom_project || __('Unknown Project');
                let site_name = parent_data.message.custom_site || __('Unknown Site');

                // Structured, user-friendly message
                let message = `
                    <div>
                        <p>⚠️ <b>Conflict Detected!</b></p>
                        <p>Employee <b>${employee_id}</b> is already assigned:</p>
                        <ul>
                            <li><b>Project:</b> ${project_name}</li>
                            <li><b>Site:</b> ${site_name}</li>
                        </ul>
                        <p>Please select another employee or remove this assignment.</p>
                    </div>
                `;

                frappe.msgprint({
                    title: __('Employee Assignment Conflict'),
                    indicator: 'red',
                    message: message
                });

                // Optional: also show a small alert at the bottom
                frappe.show_alert({
                    message: __("Conflict: Employee {0} already assigned!", [employee_id]),
                    indicator: 'red',
                    duration: 7
                });
            }
            return true; 
        }
    } catch (e) {
        console.error(e);
    }
    return false; 
}

function update_quantity(frm) {
    let count = (frm.doc.employee_table || []).filter(r => r.employee).length;
    if (frm.doc.quantity !== count) {
        frm.set_value("quantity", count);
    }
}