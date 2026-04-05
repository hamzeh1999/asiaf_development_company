"""
report_permission_patch.py
==========================

Monkey-patches `frappe.desk.query_report.get_filtered_data` so that
all Script Reports referencing the `Project` DocType (or containing a
Project link column) are filtered by this app's custom
`permission_query_conditions`.

This ensures Script Reports using `frappe.db.get_all` or `frappe.db.sql`
respect Project-level permissions without modifying each report.

Usage
-----
Add to `hooks.py` → `boot_session`:

    boot_session = [
        "asiaf_development_company.asiaf_development_company.project.report_permission_patch.boot",
    ]

`apply()` can also be called directly if boot-safe usage is not needed.

Thread-safety
-------------
Idempotent: safe to call multiple times; prevents double-patching.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import frappe
import frappe.desk.query_report as _qr_mod

if TYPE_CHECKING:
    from collections.abc import Sequence

# ---------------------------------------------------------------------------
# Module-level logger — use Frappe's logger so output lands in
# frappe.log / site logs rather than stdout.
# ---------------------------------------------------------------------------
_logger = logging.getLogger("frappe.report_permission_patch")

# ---------------------------------------------------------------------------
# Sentinel so we never double-patch across hot-reloads / multiple apply() calls.
# ---------------------------------------------------------------------------
_PATCH_APPLIED: bool = False

# ---------------------------------------------------------------------------
# Keep a reference to the *original* function before we replace it.
# Stored at import time so it is never accidentally overwritten.
# ---------------------------------------------------------------------------
_orig_get_filtered_data = _qr_mod.get_filtered_data


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def apply() -> None:
    """
    Replace ``frappe.desk.query_report.get_filtered_data`` with the
    patched version.

    Idempotent: safe to call more than once.
    """
    global _PATCH_APPLIED  # noqa: PLW0603

    if _PATCH_APPLIED:
        _logger.debug("report_permission_patch: already applied, skipping.")
        return

    _qr_mod.get_filtered_data = _patched_get_filtered_data
    _PATCH_APPLIED = True
    _logger.info("report_permission_patch: get_filtered_data patched successfully.")


def boot(bootinfo) -> None:
    """
    Boot-safe entry point intended for ``hooks.py → boot_session``.

    Frappe calls boot_session functions with a ``bootinfo`` argument.
    We don't use it, but the signature must accept it.

    Calls ``apply()`` and catches all exceptions so a patch failure
    never prevents the site from starting. Errors are logged with full
    tracebacks so they are visible in the Frappe site log.

    hooks.py example::

        boot_session = [
            "asiaf_development_company.asiaf_development_company"
            ".project.report_permission_patch.boot",
        ]
    """
    try:
        apply()
    except Exception:
        _logger.exception(
            "report_permission_patch: apply() raised an unexpected error — "
            "Project-level report filtering is NOT active."
        )


# ---------------------------------------------------------------------------
# Cache helper
# ---------------------------------------------------------------------------

def _get_allowed_projects() -> frozenset[str]:
    """
    Return the Project names visible to the current user.

    Result is cached per-user on ``frappe.local`` for the lifetime of
    the current request — so multiple reports on the same page only
    trigger one DB query per user instead of one per report.

    The cache key is scoped to the current user to prevent any risk of
    one user's allowed projects leaking to another user.
    """
    # Per-user cache key — critical for security, prevents cross-user leaks.
    cache_key = f"_report_permission_patch_{frappe.session.user}"

    # Safe access to frappe.local.cache — structure may vary across
    # Frappe versions so we never assume it exists or is a dict.
    cache = getattr(frappe.local, "cache", {})

    cached = cache.get(cache_key) if isinstance(cache, dict) else None
    if cached is not None:
        return cached

    allowed = frozenset(
        frappe.get_list("Project", pluck="name", limit_page_length=0)
    )

    if isinstance(cache, dict):
        cache[cache_key] = allowed

    return allowed


# ---------------------------------------------------------------------------
# Patched implementation
# ---------------------------------------------------------------------------

def _patched_get_filtered_data(
    ref_doctype: str,
    columns: Sequence[dict],
    data: Sequence,
    user: str,
) -> list:
    """
    Wrapper around the original ``get_filtered_data`` that additionally
    enforces Project-level permissions for the requesting user.

    Parameters
    ----------
    ref_doctype:
        The primary DocType associated with the report.
    columns:
        Column definitions returned by the report script.
    data:
        Raw rows returned by the report script.
    user:
        The Frappe username executing the report.

    Returns
    -------
    list
        Filtered rows the user is permitted to see.
    """
    # ------------------------------------------------------------------
    # 1. Run the original Frappe filtering first (role-permission checks,
    #    hidden field stripping, etc.).
    # ------------------------------------------------------------------
    try:
        result = _orig_get_filtered_data(ref_doctype, columns, data, user)
    except Exception:
        _logger.exception(
            "report_permission_patch: original get_filtered_data raised "
            "an unexpected exception (ref_doctype=%r, user=%r).",
            ref_doctype,
            user,
        )
        raise  # Never silently swallow — let Frappe handle the error response.

    # ------------------------------------------------------------------
    # 2. Early-exit guards.
    # ------------------------------------------------------------------
    if not result:
        return result

    if not user:
        _logger.warning(
            "report_permission_patch: empty user received; skipping "
            "Project permission filter (ref_doctype=%r).",
            ref_doctype,
        )
        return result

    # Administrators are not subject to record-level restrictions.
    if user == "Administrator":
        return result

    # ------------------------------------------------------------------
    # 3. Determine whether this report surfaces Project data at all.
    # ------------------------------------------------------------------
    project_field = _find_project_field(ref_doctype, columns)
    if not project_field:
        return result

    # ------------------------------------------------------------------
    # 4. Fetch the set of Project names visible to this user.
    #    Cached per-user per-request so multiple reports on the same
    #    page only hit the DB once per user.
    # ------------------------------------------------------------------
    try:
        allowed_projects = _get_allowed_projects()
    except Exception:
        _logger.exception(
            "report_permission_patch: failed to fetch allowed projects "
            "for user %r; returning empty result for safety.",
            user,
        )
        # Fail-closed: return nothing rather than leaking data.
        return []

    # ------------------------------------------------------------------
    # 5. Filter rows: keep rows whose project value is in the allowed
    #    set OR whose project cell is empty / None (project-agnostic rows).
    #    Non-dict rows are skipped explicitly and logged — they are not
    #    silently dropped.
    # ------------------------------------------------------------------
    filtered: list = []
    skipped: int = 0

    for row in result:
        if not isinstance(row, dict):
            skipped += 1
            continue

        val = row.get(project_field)
        if not val or val in allowed_projects:
            filtered.append(row)

    if skipped:
        _logger.warning(
            "report_permission_patch: skipped %d non-dict row(s) "
            "(ref_doctype=%r) — report may be returning unexpected row types.",
            skipped,
            ref_doctype,
        )

    _logger.debug(
        "report_permission_patch: filtering complete | user=%s | "
        "doctype=%s | field=%s | before=%d | after=%d",
        user,
        ref_doctype,
        project_field,
        len(result),
        len(filtered),
    )

    return filtered


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _find_project_field(
    ref_doctype: str,
    columns: Sequence[dict],
) -> str | None:
    """
    Return the fieldname that links to the Project DocType, or ``None``
    if this report does not reference Projects.

    Detection order
    ---------------
    1. A column with ``fieldtype == "Link"`` and ``options == "Project"``.
    2. Any column whose ``fieldname`` is literally ``"project"``.
    3. If *ref_doctype* is ``"Project"`` itself, fall back to ``"name"``
       (the primary-key column).

    Parameters
    ----------
    ref_doctype:
        The primary DocType of the report.
    columns:
        Column definition dicts from the report script.

    Returns
    -------
    str | None
        Fieldname to use when extracting the Project value from each row,
        or ``None`` if no Project column was found.
    """
    for col in columns:
        if not isinstance(col, dict):
            continue

        # Explicit Link → Project column.
        if col.get("fieldtype") == "Link" and col.get("options") == "Project":
            return col.get("fieldname")

        # Implicit convention: fieldname == "project".
        if col.get("fieldname") == "project":
            return "project"

    # If the report *is* a Project report, its primary key is the Project name.
    if ref_doctype == "Project":
        return "name"

    return None