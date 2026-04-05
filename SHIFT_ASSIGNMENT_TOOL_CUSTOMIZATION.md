# Shift Assignment Tool Customization - Complete Documentation

## Overview

The Shift Assignment Tool (a Single DocType in HRMS) has been extended with custom fields to support project-based shift management. Since Single DocTypes cannot be customized via the standard UI, the implementation uses custom field configurations, client scripts, and server-side API methods to inject the desired behavior.

**Date**: April 2, 2026  
**Status**: Production-Ready  
**Compatibility**: Frappe HRMS with custom Project and Shift Location enhancements

---

## Custom Fields Added

### 1. `custom_project` (Link → Project)
- **Position**: Right after `shift_location`
- **Mandatory**: When action is "Assign Shift"
- **Behavior**: 
  - Filters `shift_location` dropdown to show only locations linked to the selected project
  - Clears location field when project changes
  - Initial field to be selected in the workflow

### 2. `custom_administrative_region` (Link → Administrative Region)
- **Position**: Right after `custom_project`
- **Read-only**: Yes (auto-populated from selected shift location)
- **Behavior**: 
  - Automatically populated when a shift location is selected
  - Shows the administrative region where the shift location is situated
  - Useful for reporting and filtering

### 3. `custom_city` (Link → City)
- **Position**: Right after `custom_administrative_region`
- **Read-only**: Yes (auto-populated from selected shift location)
- **Behavior**: 
  - Automatically populated when a shift location is selected
  - Shows the city where the shift location is situated
  - Useful for reporting and geolocation-based filtering

---

## Implementation Files

### 1. **Custom Field Configuration**
**Path**: `asiaf_development_company/asiaf_development_company/custom/shift_assignment_tool.json`

Contains:
- 3 custom field definitions with full Frappe metadata
- Field order property setter to ensure correct UI layout
- All fields are hidden unless action is "Assign Shift"

**Key Attributes**:
```json
{
  "fieldname": "custom_project",
  "fieldtype": "Link",
  "options": "Project",
  "mandatory_depends_on": "eval:doc.action === \"Assign Shift\"",
  "depends_on": "eval:doc.action === \"Assign Shift\"",
  "read_only": false,
  "no_copy": true
}
```

### 2. **Client Script - Shift Assignment Tool**
**Path**: `asiaf_development_company/public/js/shift_assignment_tool.js`

Purpose: Main form event handler for Shift Assignment Tool

**Events Handled**:
- `setup(frm)`: Initialize shift location query filter
- `onload(frm)`: Set up initial field states
- `refresh(frm)`: Reload locations and auto-populate fields on form refresh
- `action(frm)`: Handle action change (show/hide custom fields)
- `custom_project(frm)`: Load filtered locations when project selected
- `shift_location(frm)`: Auto-populate region and city from location

**Features**:
- Comprehensive error handling
- Field reset logic when parent field changes
- Graceful handling of missing data

### 3. **Shared Utility Library**
**Path**: `asiaf_development_company/public/js/shift_utils.js`

Global utility object `window.ShiftUtils` with reusable functions:

#### `toggle_custom_fields(frm)`
- Controls visibility of custom fields based on action selection
- Ensures fields only appear when action is "Assign Shift"

#### `setup_location_query(frm)`
- Sets up the dropdown filter for shift_location field
- Only allows locations that are linked to the selected project

#### `toggle_shift_location(frm)`
- Enables/disables shift_location field based on project selection
- Ensures logical workflow (project → location → region/city)

#### `load_project_locations(frm)`
- Fetches all shift locations linked to the selected project via API
- Handles API errors gracefully
- Clears invalid selections automatically

#### `fetch_location_details(frm)`
- Retrieves administrative region and city from selected shift location
- Handles both Link and Data field types
- Uses Promise.all for efficient parallel data fetching

### 4. **Server-Side API**
**Path**: `asiaf_development_company/asiaf_development_company/api.py`

#### Existing Function: `get_project_shift_locations(project)`
```python
@frappe.whitelist()
def get_project_shift_locations(project):
    """Return the list of Shift Location names linked to a Project's site table."""
    if not project:
        return []

    sites = frappe.get_all(
        "Project Site Link",
        filters={"parent": project, "parenttype": "Project", "parentfield": "custom_site"},
        fields=["site"],
        ignore_permissions=True,
    )

    return [row.site for row in sites if row.site]
```

**Purpose**: Filters shift locations by project without loading all data

### 5. **Hooks Configuration**
**Path**: `asiaf_development_company/hooks.py`

Updated `doctype_js` to include:
```python
doctype_js = {
    # ... existing entries ...
    "Shift Assignment Tool": "public/js/shift_assignment_tool.js"
}
```

---

## User Workflow

```
┌─────────────────────┐
│ Open Shift          │
│ Assignment Tool     │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│ Select Action:      │
│ "Assign Shift" ✓    │
│ (custom fields      │
│  now visible)       │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│ Select Project      │
│ [Project ID]        │
└──────────┬──────────┘
           │ (API triggers)
           ↓
┌─────────────────────┐
│ Select Shift        │
│ Location (FILTERED) │ ← Only locations linked to project
│ [Location]          │
└──────────┬──────────┘
           │ (Auto-populate)
           ↓
┌─────────────────────┐
│ Admin Region:       │
│ [Read-Only, Auto]   │
│                     │
│ City:               │
│ [Read-Only, Auto]   │
└──────────┬──────────┘
           │ (Continue with standard fields)
           ↓
┌─────────────────────┐
│ Proceed with bulk   │
│ assignment as usual │
└─────────────────────┘
```

---

## Technical Details

### Field Dependencies

This implementation uses Frappe's `depends_on` and `mandatory_depends_on` evaluators:

```javascript
depends_on: "eval:doc.action === \"Assign Shift\""
```

This ensures:
1. Fields are visible ONLY when "Assign Shift" is selected
2. User cannot select these fields for other actions
3. Validation automatically handles mandatory requirements

### Data Flow

1. **Project Selection** → Triggers `load_project_locations()`
2. **Location Selection** → Triggers `fetch_location_details()`
3. **Auto-Population** → Administrative Region and City filled
4. **Standard Workflow** → Assignment proceeds normally

### Error Handling

- **Invalid Project**: Returns empty location list (user cannot proceed)
- **Deleted Project**: Gracefully handled, fields cleared
- **Missing Location Details**: Shows empty for admin region/city
- **API Timeouts**: Displays user-friendly error message

---

## Production Checklist

✅ **Custom Fields Configured**
- Correct field types (Link fields with proper options)
- Proper insert_after positioning
- Field visibility controls (depends_on)

✅ **Client Scripts Deployed**
- shift_assignment_tool.js registered in hooks.py
- ShiftUtils accessible globally
- Event handlers comprehensive

✅ **Server-Side API**
- `get_project_shift_locations()` available and secure
- Uses @frappe.whitelist() decorator
- Handles empty/invalid inputs gracefully

✅ **Code Quality**
- JSDoc comments added
- Error handling implemented
- No breaking changes to existing functionality

✅ **Performance Optimized**
- Minimal API calls
- Efficient Promise.all() for parallel loading
- Dropdown filtering prevents large datasets from loading

---

## Backwards Compatibility

✅ **No Breaking Changes**
- Other actions ("Assign Shift Schedule", "Process Shift Requests") unchanged
- Existing shift assignment logic unaffected
- Single DocType serialization preserved

---

## Deployment Instructions

### 1. Update Custom JSON
```bash
cd frappe-bench
dock_compose exec frappe bench --site=mysite.local migrate
```

### 2. Clear Cache
```bash
# Browser cache: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
# or
bench clear-cache
```

### 3. Test Workflow
1. Open Shift Assignment Tool
2. Select "Assign Shift" action
3. Verify custom fields appear
4. Select a project
5. Verify shift_location dropdown filters correctly
6. Select a location
7. Verify admin region and city auto-populate

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Custom fields not visible | Clear browser cache & refresh |
| Location dropdown empty | Verify project has linked sites |
| Admin region/city not auto-populating | Check shift_location custom field values |
| "Could not load locations" error | Verify get_project_shift_locations() method exists |

---

## API Reference

### Client-Side (JavaScript)

**Global Object**: `window.ShiftUtils`

```javascript
// Toggle field visibility
ShiftUtils.toggle_custom_fields(frm);

// Set up location filter
ShiftUtils.setup_location_query(frm);

// Control shift_location read-only state
ShiftUtils.toggle_shift_location(frm);

// Fetch locations for project
ShiftUtils.load_project_locations(frm);

// Auto-populate region/city from location
ShiftUtils.fetch_location_details(frm);
```

### Server-Side (Python)

```python
# Method: get_project_shift_locations
# Returns: List[str] - Shift Location names linked to project

result = frappe.call({
    'method': 'asiaf_development_company.asiaf_development_company.api.get_project_shift_locations',
    'args': {'project': 'PROJECT-001'}
})
# result.message = ['Location A', 'Location B', ...]
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-02 | Initial production release with 3 custom fields |

---

## Support & Maintenance

For issues or enhancements:
1. Check [SHIFT_ASSIGNMENT_TOOL_QUICK_REFERENCE.md](SHIFT_ASSIGNMENT_TOOL_QUICK_REFERENCE.md)
2. Review logs in browser console (F12 → Console tab)
3. Check server logs in `frappe-bench/logs/`

---

## License

This customization follows the same license as the parent application (Frappe HRMS).
