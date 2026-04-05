# Copyright (c) 2026, Asiaf Development Company and contributors
# For license information, please see license.txt

"""
task_permissions.py
===================
Permission query hook for the **Task** DocType.

Ensures that users only see Tasks belonging to Projects they are
authorised to access, consistent with the access model enforced by
``project_restrictions.py``.

Access tiers (evaluated top-to-bottom, first match wins)
---------------------------------------------------------
1. **System Manager / Projects Manager**
   Full unrestricted access — no row-level filter applied.

2. **Project Manager**
   Sees Tasks for every Project where:
   a. They are the assigned ``custom_project_manager`` (Employee match), OR
   b. They hold a ``User Permission`` for the Project (granted by
      ``project_restrictions._grant_new_pm_permission``), OR
   c. They appear in the Project's ``users`` child table (User match).

3. **Regular employee** (has an Employee record, no elevated role)
   Sees Tasks only for Projects where:
   a. They hold a ``User Permission`` for the Project, OR
   b. They appear in the Project's ``users`` child table.

4. **No employee record / unresolvable user**
   No Tasks visible (``1=0``).

Hook registration (hooks.py)
-----------------------------
    permission_query_conditions = {
        "Task": (
            "asiaf_development_company"
            ".asiaf_development_company"
            ".project.task_permissions.get_permission_query_conditions"
        ),
    }

Design notes
------------
* All role and employee lookups are cached within the request via
  ``frappe.get_roles()`` — safe and performant for list-view rendering.
* ``frappe.db.escape()`` is used for every value interpolated into raw
  SQL to prevent SQL injection.
* On any unexpected error the function falls back to ``1=0`` (deny all)
  and logs the traceback — a failed permission check must never grant
  more access than intended.
* Role constants are defined once at module level; if a role is renamed
  only this file needs updating.
* ``tabUser Permission`` checks mirror the grants created and cleaned up
  by ``project_restrictions._grant_new_pm_permission`` and
  ``project_restrictions._cleanup_old_pm_permission``.
"""

from __future__ import annotations

import frappe

# ── Role constants ────────────────────────────────────────────────────────────
# Must match the exact role names defined in Frappe / your app.
FULL_ACCESS_ROLES: frozenset[str] = frozenset({"System Manager", "Projects Manager"})
PROJECT_MANAGER_ROLE: str = "Project Manager"


# ── Entry point ───────────────────────────────────────────────────────────────

def get_permission_query_conditions(user: str | None = None) -> str:
    """
    Returns a raw SQL ``WHERE`` fragment that restricts the Task list to
    rows the current user is permitted to see.

    An empty string means "no restriction" (full access).
    ``"1=0"`` means "no rows visible".

    Parameters
    ----------
    user:
        The user for whom conditions are being built.  Frappe passes this
        automatically; defaults to ``frappe.session.user`` when omitted.
    """
    if not user:
        user = frappe.session.user

    # ── Basic sanity check ────────────────────────────────────────────────────
    if not user or not isinstance(user, str):
        return "1=0"

    try:
        return _build_conditions(user)

    except Exception:
        frappe.log_error(
            title="Task: Permission Query Error",
            message=frappe.get_traceback(),
        )
        # Fail closed — deny everything rather than leak data.
        return "1=0"


# ── Condition builder ─────────────────────────────────────────────────────────

def _build_conditions(user: str) -> str:
    """
    Core logic — resolves the user's roles and employee record, then
    returns the appropriate SQL fragment.
    """
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
    A Project Manager sees Tasks for any Project where they are:
      (a) the designated ``custom_project_manager`` on the Project, OR
      (b) they hold a ``User Permission`` for the Project — granted
          automatically by ``project_restrictions._grant_new_pm_permission``
          and revoked by ``project_restrictions._cleanup_old_pm_permission``, OR
      (c) listed in the Project's ``users`` child table.
    """
    escaped_user     = frappe.db.escape(user)
    escaped_employee = frappe.db.escape(employee)

    return f"""(
        EXISTS (
            SELECT 1
            FROM `tabProject`
            WHERE `tabProject`.`name` = `tabTask`.`project`
              AND `tabProject`.`custom_project_manager` = {escaped_employee}
        )
        OR EXISTS (
            SELECT 1
            FROM `tabUser Permission`
            WHERE `tabUser Permission`.`user`      = {escaped_user}
              AND `tabUser Permission`.`allow`     = 'Project'
              AND `tabUser Permission`.`for_value` = `tabTask`.`project`
        )
        OR EXISTS (
            SELECT 1
            FROM `tabProject User`
            WHERE `tabProject User`.`parent` = `tabTask`.`project`
              AND `tabProject User`.`user`   = {escaped_user}
        )
    )"""


def _conditions_for_project_user(user: str) -> str:
    """
    A regular employee sees Tasks only for Projects where:
      (a) they hold a ``User Permission`` for the Project, OR
      (b) they appear in the ``users`` child table.

    The User Permission path catches cases where an employee was granted
    access via ``project_restrictions`` without being added to the
    child table directly.
    """
    escaped_user = frappe.db.escape(user)

    return f"""(
        EXISTS (
            SELECT 1
            FROM `tabUser Permission`
            WHERE `tabUser Permission`.`user`      = {escaped_user}
              AND `tabUser Permission`.`allow`     = 'Project'
              AND `tabUser Permission`.`for_value` = `tabTask`.`project`
        )
        OR EXISTS (
            SELECT 1
            FROM `tabProject User`
            WHERE `tabProject User`.`parent` = `tabTask`.`project`
              AND `tabProject User`.`user`   = {escaped_user}
        )
    )"""


# ── Cached lookups ────────────────────────────────────────────────────────────

def _get_user_roles(user: str) -> frozenset[str]:
    """
    Returns the full set of Frappe Roles assigned to *user*.
    Result is a ``frozenset`` for fast ``in`` / ``&`` operations.
    Uses ``frappe.get_roles()`` which is already request-cached by Frappe.
    """
    return frozenset(frappe.get_roles(user))


def _get_employee(user: str) -> str | None:
    """
    Returns the ``name`` of the Employee record linked to *user*, or
    ``None`` if no such record exists.

    Consistent with ``project_restrictions._get_user_id()`` which does
    the reverse lookup (Employee → user_id).
    """
    return (
        frappe.db.get_value("Employee", {"user_id": user}, "name") or None
    )