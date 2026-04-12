import frappe
from frappe import _


def execute(doc, method=None):
    """
    Triggered before saving the Project.
    1. Validates no duplicate sites exist in the child table (server-side guard).
    2. Validates custom_project_manager has the 'Project Manager' role.
    3. Syncs User Permissions for the custom_project_manager field.
    """
    _enforce_duplicate_site_check(doc)
    
    if doc.custom_project_manager:
        _validate_project_manager_role(doc)

    old_doc = doc.get_doc_before_save()

    if old_doc and old_doc.custom_project_manager:
        _cleanup_old_pm_permission(doc, old_doc)

    if doc.custom_project_manager:
        _grant_new_pm_permission(doc)


# ── Validation ────────────────────────────────────────────────────────────────

def _enforce_duplicate_site_check(doc):
    seen = set()
    for row in (doc.custom_site or []):
        if not row.site:
            continue
        if row.site in seen:
            frappe.throw(
                _("Duplicate site: {0} is already added to this project.").format(row.site)
            )
        seen.add(row.site)


def _validate_project_manager_role(doc):
    employee_id = doc.custom_project_manager
    
    if not employee_id:
        return
    
    if not frappe.db.exists("Employee", employee_id):
        frappe.throw(
            _("Employee {0} does not exist.").format(employee_id),
            title=_("Invalid Employee")
        )
    
    pm_user = frappe.db.get_value("Employee", employee_id, "user_id")
    
    if not pm_user:
        frappe.throw(
            _("Employee {0} has no linked system user. "
              "Only employees with an active user account can be assigned as Project Manager.").format(employee_id),
            title=_("No System User Linked")
        )
    
    user_roles = frappe.get_roles(pm_user)
    
    if "Project Manager" not in user_roles:
        frappe.throw(
            _("The selected employee ({0}) with user account ({1}) does not have the 'Project Manager' role. "
              "Please select an employee with the 'Project Manager' role assigned.").format(employee_id, pm_user),
            title=_("Invalid Role")
        )


# ── Permission helpers ────────────────────────────────────────────────────────

_ADMIN_ROLES = {"System Manager", "Projects Manager", "Tendering Manager"}


def _grant_new_pm_permission(doc):
    try:
        pm_user = frappe.db.get_value("Employee", doc.custom_project_manager, "user_id")

        if not pm_user:
            frappe.msgprint(
                _("Project Manager {0} has no linked system user. "
                  "User Permission was not created.").format(doc.custom_project_manager),
                indicator="orange",
                alert=True
            )
            return

        if _ADMIN_ROLES & set(frappe.get_roles(pm_user)):
            return

        already_exists = frappe.db.exists("User Permission", {
            "user": pm_user,
            "allow": "Project",
            "for_value": doc.name
        })

        if not already_exists:
            frappe.db.sql("""
                INSERT INTO `tabUser Permission`
                    (name, user, allow, for_value, apply_to_all_doctypes,
                     creation, modified, modified_by, owner, docstatus)
                VALUES
                    (%s, %s, 'Project', %s, 1,
                     NOW(), NOW(), 'Administrator', 'Administrator', 0)
            """, (frappe.generate_hash(length=10), pm_user, doc.name))
            frappe.db.commit()

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Grant PM Permission Error")
        frappe.msgprint(
            _("Could not create User Permission for the Project Manager. "
              "Please check the error log."),
            indicator="red",
            alert=True
        )


def _cleanup_old_pm_permission(doc, old_doc):
    try:
        old_pm = old_doc.custom_project_manager
        new_pm = doc.custom_project_manager

        if old_pm == new_pm:
            return

        old_user = frappe.db.get_value("Employee", old_pm, "user_id")
        if not old_user:
            return

        frappe.db.sql("""
            DELETE FROM `tabUser Permission`
            WHERE user = %s
            AND allow = 'Project'
            AND for_value = %s
        """, (old_user, doc.name))
        frappe.db.commit()

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Cleanup PM Permission Error")
        frappe.msgprint(
            _("Could not remove the previous Project Manager's User Permission. "
              "Please check the error log."),
            indicator="orange",
            alert=True
        )


# ── Filter Helpers ────────────────────────────────────────────────────────────

@frappe.whitelist()
def validate_employee_has_pm_role(employee_id):
    if not employee_id or not frappe.db.exists("Employee", employee_id):
        return {"has_role": False, "user_id": None, "reason": "no_employee"}

    user_id = frappe.db.get_value("Employee", employee_id, "user_id")
    if not user_id:
        return {"has_role": False, "user_id": None, "reason": "no_user"}

    user_roles = frappe.get_roles(user_id)
    return {
        "has_role": "Project Manager" in user_roles,
        "user_id": user_id,
        "reason": "" if "Project Manager" in user_roles else "no_role"
    }


@frappe.whitelist()
def get_project_managers(doctype, txt, searchfield, start, page_len, filters):
    try:
        start = int(start) if start else 0
        page_len = int(page_len) if page_len else 20
        
        query = """
            SELECT DISTINCT e.name, e.employee_name
            FROM `tabEmployee` e
            INNER JOIN `tabHas Role` hr ON e.user_id = hr.parent
            WHERE e.status = 'Active'
            AND hr.role = 'Project Manager'
            AND e.user_id IS NOT NULL
            AND e.user_id != ''
        """
        
        if txt:
            txt_filter = f"%{txt}%"
            query += " AND (e.name LIKE %s OR e.employee_name LIKE %s)"
            params = [txt_filter, txt_filter]
        else:
            params = []
        
        query += " ORDER BY e.employee_name ASC LIMIT %s, %s"
        params.extend([start, page_len])
        
        return frappe.db.sql(query, params, as_list=True)
    
    except Exception as e:
        frappe.log_error(f"Error in get_project_managers: {str(e)}\n{frappe.get_traceback()}",
                         "Project Manager Filter Error")


def cleanup_admin_user_project_permissions():
    """
    One-time utility: Remove stale Project User Permissions for admin-role users.

    Run on production:
        bench --site <site> execute \\
            asiaf_development_company.asiaf_development_company.project.project_restrictions.cleanup_admin_user_project_permissions
    """
    perms = frappe.get_all(
        "User Permission",
        filters={"allow": "Project"},
        fields=["name", "user", "for_value"],
    )

    removed = 0
    for perm in perms:
        if _ADMIN_ROLES & set(frappe.get_roles(perm["user"])):
            frappe.delete_doc("User Permission", perm["name"], ignore_permissions=True)
            frappe.db.commit()
            print(f"Removed: {perm['name']} — user={perm['user']} project={perm['for_value']}")
            removed += 1

    print(f"\nDone. Removed {removed} stale User Permission(s) for admin users.")
    return removed