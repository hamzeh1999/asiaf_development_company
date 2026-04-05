import frappe
from hrms.hr.doctype.shift_assignment_tool.shift_assignment_tool import ShiftAssignmentTool


class CustomShiftAssignmentTool(ShiftAssignmentTool):
    """
    Extends ShiftAssignmentTool to pass custom Project, Administrative
    Region, and City fields down to individual Shift Assignments during
    bulk assignment.

    Why this is needed
    ------------------
    The standard _bulk_assign creates Shift Assignment records without
    knowledge of these custom fields. We use frappe.flags as a
    request-scoped context carrier so the downstream before_insert hook
    on Shift Assignment can pick them up and stamp them on each record.

    Why frappe.flags
    ----------------
    frappe.flags is a request-scoped dict — it resets between requests
    automatically, making it safe for passing context between layers
    without polluting the DocType API or method signatures.

    Why try/finally
    ---------------
    Guarantees the flags are always cleaned up even if _bulk_assign
    raises an exception — prevents stale values from leaking into
    subsequent operations in the same request.
    """

    def _bulk_assign(self, employees):
        # Set custom fields as request-scoped flags so the
        # Shift Assignment before_insert hook can read them.
        frappe.flags.shift_tool_custom_project = self.custom_project
        frappe.flags.shift_tool_custom_administrative_region = self.custom_administrative_region
        frappe.flags.shift_tool_custom_city = self.custom_city

        try:
            super()._bulk_assign(employees)
        finally:
            # Always clean up — even if bulk assign fails midway.
            frappe.flags.pop("shift_tool_custom_project", None)
            frappe.flags.pop("shift_tool_custom_administrative_region", None)
            frappe.flags.pop("shift_tool_custom_city", None)