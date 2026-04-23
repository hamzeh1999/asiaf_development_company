import frappe
from frappe import _


def get_permission_query_conditions(user: str | None = None) -> str | None:
    """
    Permission query conditions for Project doctype.

    - Admins (System Manager, Projects Manager, Tendering Manager): full access
    - Project Manager: scoped to assigned projects (custom_project_manager or Project User table)
    - Everything else: delegated to Frappe Role Permission Manager
    """
    # ── Resolve user ──────────────────────────────────────────────────────────
    user = user or frappe.session.user

    if not user or not isinstance(user, str) or user == "Guest":
        return "1=0"

    try:
        user_roles: set[str] = set(frappe.get_roles(user))

        # ── Admins: full visibility ───────────────────────────────────────────
        if _is_admin(user_roles):
            return "1=1"

        # ── Project Manager: scoped visibility ───────────────────────────────
        if "Project Manager" in user_roles:
            return _get_project_manager_conditions(user, user_roles)

        # ── Everything else: Frappe handles it ───────────────────────────────
        return None

    except Exception:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="Project Permission Query Error"
        )
        return None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_admin(user_roles: set[str]) -> bool:
    return bool({"System Manager", "Projects Manager", "Tendering Manager"} & user_roles)


def _get_project_manager_conditions(user: str, user_roles: set[str]) -> str | None:
    """
    Returns scoped SQL for Project Manager role.
    Falls back to None (Frappe default) if no Employee record is linked.
    """
    employee = frappe.db.get_value(
        "Employee",
        {"user_id": user, "status": "Active"},  # only active employees
        "name",
        cache=True  # cache to avoid repeated DB hits
    )

    if not employee:
        frappe.log_error(
            message=(
                f"User '{user}' has the 'Project Manager' role "
                f"but has no linked active Employee record. "
                f"Falling back to Frappe default permissions."
            ),
            title="Project Permission – Missing Employee Record"
        )
        return None

    escaped_user     = frappe.db.escape(user)
    escaped_employee = frappe.db.escape(employee)

    return f"""
        (
            `tabProject`.custom_project_manager = {escaped_employee}
            OR EXISTS (
                SELECT 1
                FROM `tabProject User`
                WHERE `tabProject User`.parent = `tabProject`.name
                AND   `tabProject User`.user   = {escaped_user}
            )
        )
    """