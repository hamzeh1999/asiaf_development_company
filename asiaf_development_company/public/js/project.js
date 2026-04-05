frappe.ui.form.on("Project", {
    refresh(frm) {
        // 1. Filter Project Manager: Show only Employees who have the 'Project Manager' role
        // Use server method for reliable filtering
        frm.set_query("custom_project_manager", function() {
            return {
                query: "asiaf_development_company.asiaf_development_company.project.project_restrictions.get_project_managers"
            };
        });

        // 2. Apply your existing site filters
        applySiteFilter(frm);
    },

    validate(frm) {
        // 3. Keep your existing duplicate check
        enforceDuplicateSiteCheck(frm);
    },

    // 4. NEW: Validate Project Manager role when field changes
    custom_project_manager(frm) {
        validateProjectManagerRole(frm);
    }
});

frappe.ui.form.on("Project Site", {
    site(frm) {
        applySiteFilter(frm);
    },
    custom_site_remove(frm) {
        applySiteFilter(frm);
    }
});

// --- HELPER FUNCTIONS ---

/**
 * NEW: Validate that the selected employee has the 'Project Manager' role
 * Provides immediate client-side feedback to the user
 */
function validateProjectManagerRole(frm) {
    const employeeId = frm.doc.custom_project_manager;
    
    // If field is cleared, no validation needed
    if (!employeeId) {
        return;
    }

    // Use whitelisted server method to check role (avoids Has Role permission issue)
    frappe.call({
        method: "asiaf_development_company.asiaf_development_company.project.project_restrictions.validate_employee_has_pm_role",
        args: { employee_id: employeeId },
        callback: function(r) {
            if (!r.message) return;

            const result = r.message;

            if (result.reason === "no_user") {
                frappe.msgprint({
                    title: __("No System User"),
                    message: __("Employee {0} has no linked system user. Only employees with an active user account can be assigned as Project Manager.", [employeeId]),
                    indicator: "orange"
                });
                frm.set_value("custom_project_manager", "");
            } else if (!result.has_role) {
                frappe.msgprint({
                    title: __("Invalid Role"),
                    message: __("Employee {0} (user: {1}) does not have the 'Project Manager' role. " +
                        "Only users with the 'Project Manager' role can be assigned as Project Manager.",
                        [employeeId, result.user_id]),
                    indicator: "red"
                });
                frm.set_value("custom_project_manager", "");
            }
        }
    });
}

/**
 * Filter: Hide sites already selected in the child table
 */
function applySiteFilter(frm) {
    if (!frm.fields_dict.custom_site) return;

    frm.fields_dict["custom_site"].grid.get_field("site").get_query = function () {
        let selected = (frm.doc.custom_site || [])
            .map(row => row.site)
            .filter(Boolean);

        return {
            filters: [["Shift Location", "name", "not in", selected]]
        };
    };
}

/**
 * Integrity: Block save if a duplicate site exists in the grid
 */
function enforceDuplicateSiteCheck(frm) {
    let seen = new Set();
    let rows = frm.doc.custom_site || [];
    
    for (let row of rows) {
        if (!row.site) continue;
        if (seen.has(row.site)) {
            frappe.validated = false;
            frappe.throw(__("Duplicate site: {0} is already added.", [row.site]));
            return;
        }
        seen.add(row.site);
    }
}