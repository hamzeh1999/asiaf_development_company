import frappe

_logger = frappe.logger("shift_assignment")


def set_custom_project_from_tool(doc, method):
    """
    Stamp custom_project, custom_administrative_region, and custom_city
    on a new Shift Assignment from one of three sources (in priority order):

    1. frappe.flags — set by CustomShiftAssignmentTool._bulk_assign
    2. Parent Shift Schedule Assignment — when auto-created from a schedule
    3. Shift Assignment Tool single doc — direct fallback
    """
    # Skip if already set or not a new record.
    if doc.custom_project or not doc.is_new():
        return

    # ------------------------------------------------------------------
    # 1. Flags set by CustomShiftAssignmentTool._bulk_assign
    # ------------------------------------------------------------------
    project = frappe.flags.get("shift_tool_custom_project")
    if project:
        doc.custom_project = project
        doc.custom_administrative_region = frappe.flags.get("shift_tool_custom_administrative_region")
        doc.custom_city = frappe.flags.get("shift_tool_custom_city")
        return

    # ------------------------------------------------------------------
    # 2. Inherit from parent Shift Schedule Assignment
    # ------------------------------------------------------------------
    if doc.shift_schedule_assignment:
        try:
            schedule = frappe.get_cached_doc("Shift Schedule Assignment", doc.shift_schedule_assignment)
            if schedule.custom_project:
                doc.custom_project = schedule.custom_project
                doc.custom_administrative_region = getattr(schedule, "custom_administrative_region", None)
                doc.custom_city = getattr(schedule, "custom_city", None)
                return
        except Exception:
            _logger.exception(
                "set_custom_project_from_tool: failed to load "
                "Shift Schedule Assignment %r for Shift Assignment %r.",
                doc.shift_schedule_assignment,
                doc.name,
            )

    # ------------------------------------------------------------------
    # 3. Fallback: Shift Assignment Tool single doc
    # ------------------------------------------------------------------
    try:
        tool = frappe.get_cached_doc("Shift Assignment Tool")
        if tool.action == "Assign Shift" and tool.custom_project:
            doc.custom_project = tool.custom_project
            doc.custom_administrative_region = getattr(tool, "custom_administrative_region", None)
            doc.custom_city = getattr(tool, "custom_city", None)
    except Exception:
        _logger.exception(
            "set_custom_project_from_tool: failed to load "
            "Shift Assignment Tool for Shift Assignment %r.",
            doc.name,
        )