import frappe
from typing import List, Optional

@frappe.whitelist()
def get_project_shift_locations(project: Optional[str]) -> List[str]:
    """
    Return a list of Shift Location names linked to a Project's custom site table.

    Parameters
    ----------
    project : str | None
        Name of the Project.

    Returns
    -------
    List[str]
        List of site names. Returns empty list if no sites or project is None.

    Notes
    -----
    - Verifies user has read permission on the Project.
    - Uses ignore_permissions=True safely for child table access.
    - Implements per-request caching to reduce repeated DB queries.
    """
    if not project:
        return []

    # Check Project read permission
    if not frappe.has_permission("Project", "read", project):
        frappe.throw(frappe._("Not permitted"), frappe.PermissionError)

    # Per-request cache key
    cache_key = f"_project_shift_sites_{project}_{frappe.session.user}"
    cache = getattr(frappe.local, "cache", {})
    if isinstance(cache, dict) and cache_key in cache:
        return cache[cache_key]

    # Fetch linked sites from child table
    sites = frappe.get_all(
        "Project Site Link",
        filters={
            "parent": project,
            "parenttype": "Project",
            "parentfield": "custom_site",
        },
        pluck="site",
        ignore_permissions=True,
    )

    result = [site for site in sites if site]

    # Cache for the current request
    if isinstance(cache, dict):
        cache[cache_key] = result

    return result