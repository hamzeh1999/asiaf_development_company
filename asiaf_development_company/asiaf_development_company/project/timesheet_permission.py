# Copyright (c) 2026, Asiaf Development Company and contributors
# For license information, please see license.txt

"""
timesheet_permissions.py
========================
Permission query hook for the **Timesheet** DocType.

Ensures that users only see Timesheets they are authorised to access,
consistent with the access model enforced by ``project_restrictions.py``.

Access tiers (evaluated top-to-bottom, first match wins)
---------------------------------------------------------
1. **System Manager / Projects Manager**
   Full unrestricted access — no row-level filter applied.

2. **Project Manager**
   Sees Timesheets where:
   a. They are the owner of the Timesheet, OR
   b. The Timesheet contains a detail line linked to a Project where
      they are the ``custom_project_manager`` (Employee match), OR
   c. The Timesheet contains a detail line linked to a Project where
      they hold a ``User Permission``, OR
   d. The Timesheet contains a detail line linked to a Project where
      they appear in the ``users`` child table.

3. **Regular employee** (has an Employee record, no elevated role)
   Sees Timesheets where:
   a. They are the owner of the Timesheet, OR
   b. The Timesheet contains a detail line linked to a Project where
      they hold a ``User Permission``, OR
   c. The Timesheet contains a detail line linked to a Project where
      they appear in the ``users`` child table.

4. **No employee record / unresolvable user**
   No Timesheets visible (``1=0``).

Hook registration (hooks.py)
-----------------------------
    permission_query_conditions = {
        "Timesheet": (
            "asiaf_development_company"
            ".asiaf_development_company"
            ".project.timesheet_permissions.get_permission_query_conditions"
        ),
    }
"""

from __future__ import annotations

import frappe

# ── Role constants ────────────────────────────────────────────────────────────
FULL_ACCESS_ROLES: frozenset[str] = frozenset({"System Manager", "Projects Manager"})
PROJECT_MANAGER_ROLE: str = "Project Manager"


# ── Entry point ───────────────────────────────────────────────────────────────

def get_permission_query_conditions(user: str | None = None) -> str:
    """
    Returns a raw SQL ``WHERE`` fragment that restricts the Timesheet list
    to rows the current user is permitted to see.

    An empty string means "no restriction" (full access).
    ``"1=0"`` means "no rows visible".
    """
    if not user:
        user = frappe.session.user

    if not user or not isinstance(user, str):
        return "1=0"

    try:
        return _build_conditions(user)

    except Exception:
        frappe.log_error(
            title="Timesheet: Permission Query Error",
            message=frappe.get_traceback(),
        )
        return "1=0"


# ── Condition builder ─────────────────────────────────────────────────────────

def _build_conditions(user: str) -> str:
    user_roles = _get_user_roles(user)

    # ── Tier 1: Full access roles ─────────────────────────────────────────────
    if user_roles & FULL_ACCESS_ROLES:
        return ""

    employee = _get_employee(user)

    # ── Tier 2: Project Manager ───────────────────────────────────────────────
    if PROJECT_MANAGER_ROLE in user_roles and employee:
        return _conditions_for_project_manager(user, employee)

    # ── Tier 3: Regular employee ──────────────────────────────────────────────
    if employee:
        return _conditions_for_project_user(user)

    # ── Tier 4: No employee record — deny all ─────────────────────────────────
    return "1=0"


# ── SQL fragment builders ─────────────────────────────────────────────────────

def _conditions_for_project_manager(user: str, employee: str) -> str:
    """
    A Project Manager sees Timesheets they own, plus any Timesheet with
    a detail line tied to a Project they manage or are a member of.
    """
    escaped_user     = frappe.db.escape(user)
    escaped_employee = frappe.db.escape(employee)

    return f"""(
        `tabTimesheet`.`owner` = {escaped_user}
        OR EXISTS (
            SELECT 1
            FROM `tabTimesheet Detail`
            WHERE `tabTimesheet Detail`.`parent` = `tabTimesheet`.`name`
              AND (
                  EXISTS (
                      SELECT 1
                      FROM `tabProject`
                      WHERE `tabProject`.`name` = `tabTimesheet Detail`.`project`
                        AND `tabProject`.`custom_project_manager` = {escaped_employee}
                  )
                  OR EXISTS (
                      SELECT 1
                      FROM `tabUser Permission`
                      WHERE `tabUser Permission`.`user`      = {escaped_user}
                        AND `tabUser Permission`.`allow`     = 'Project'
                        AND `tabUser Permission`.`for_value` = `tabTimesheet Detail`.`project`
                  )
                  OR EXISTS (
                      SELECT 1
                      FROM `tabProject User`
                      WHERE `tabProject User`.`parent` = `tabTimesheet Detail`.`project`
                        AND `tabProject User`.`user`   = {escaped_user}
                  )
              )
        )
    )"""


def _conditions_for_project_user(user: str) -> str:
    """
    A regular employee sees Timesheets they own, plus any Timesheet with
    a detail line tied to a Project they have access to.
    """
    escaped_user = frappe.db.escape(user)

    return f"""(
        `tabTimesheet`.`owner` = {escaped_user}
        OR EXISTS (
            SELECT 1
            FROM `tabTimesheet Detail`
            WHERE `tabTimesheet Detail`.`parent` = `tabTimesheet`.`name`
              AND (
                  EXISTS (
                      SELECT 1
                      FROM `tabUser Permission`
                      WHERE `tabUser Permission`.`user`      = {escaped_user}
                        AND `tabUser Permission`.`allow`     = 'Project'
                        AND `tabUser Permission`.`for_value` = `tabTimesheet Detail`.`project`
                  )
                  OR EXISTS (
                      SELECT 1
                      FROM `tabProject User`
                      WHERE `tabProject User`.`parent` = `tabTimesheet Detail`.`project`
                        AND `tabProject User`.`user`   = {escaped_user}
                  )
              )
        )
    )"""


# ── Cached lookups ────────────────────────────────────────────────────────────

def _get_user_roles(user: str) -> frozenset[str]:
    """
    Uses ``frappe.get_roles()`` which is already request-cached by Frappe.
    """
    return frozenset(frappe.get_roles(user))


def _get_employee(user: str) -> str | None:
    """
    Returns the Employee ``name`` linked to *user*, or ``None``.
    """
    return (
        frappe.db.get_value("Employee", {"user_id": user}, "name") or None
    )