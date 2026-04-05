import frappe


def get_permission_query_conditions(user=None):
    if not user:
        user = frappe.session.user

    if not user or not isinstance(user, str):
        return "1=0"

    try:
        user_roles = frappe.get_roles(user)
        escaped_user = frappe.db.escape(user)

        # ── Full visibility ───────────────────────────────────────────────────
        admin_roles = {"System Manager", "Projects Manager", "Tendering Manager"}
        if admin_roles & set(user_roles):
            return ""

        # ── Resolve Employee record ───────────────────────────────────────────
        employee = frappe.db.get_value("Employee", {"user_id": user}, "name")

        restricted_roles = {"Project Manager", "Projects User"}
        has_restricted_role = bool(restricted_roles & set(user_roles))

        if has_restricted_role:
            if not employee:
                frappe.log_error(
                    message=(
                        f"User '{user}' has a restricted Project role "
                        f"({', '.join(r for r in restricted_roles if r in user_roles)}) "
                        f"but has no linked Employee record. Access denied."
                    ),
                    title="Project Permission – Missing Employee Record"
                )
                return "1=0"

            escaped_employee = frappe.db.escape(employee)
            return f"""
            (
                `tabProject`.custom_project_manager = {escaped_employee}
                OR EXISTS (
                    SELECT 1 FROM `tabProject User`
                    WHERE parent = `tabProject`.name
                    AND user = {escaped_user}
                )
            )
            """

        # ── General staff fallback ────────────────────────────────────────────
        if employee:
            return f"""
            EXISTS (
                SELECT 1 FROM `tabProject User`
                WHERE parent = `tabProject`.name
                AND user = {escaped_user}
            )
            """

        # ── No access ─────────────────────────────────────────────────────────
        return "1=0"

    except Exception:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="Project Permission Query Error"
        )
        return "1=0"