frappe.ui.form.on('Asset', {
    custom__last_maintenance_date: function(frm) {
        calculate_next_date(frm);
    },

    custom_maintenance_interval: function(frm) {
        calculate_next_date(frm);
    },

    custom_maintenance_frequency_type: function(frm) {
        calculate_next_date(frm);
    }
});

function calculate_next_date(frm) {
    if (
        !frm.doc.custom__last_maintenance_date ||
        !frm.doc.custom_maintenance_interval ||
        !frm.doc.custom_maintenance_frequency_type
    ) {
        return;
    }

    let last_date = frappe.datetime.str_to_obj(frm.doc.custom__last_maintenance_date);
    let interval = parseInt(frm.doc.custom_maintenance_interval, 10);
    let frequency = frm.doc.custom_maintenance_frequency_type;

    if (isNaN(interval) || interval <= 0) {
        return;
    }

    if (frequency === "Daily") {
        last_date.setDate(last_date.getDate() + interval);
    } else if (frequency === "Weekly") {
        last_date.setDate(last_date.getDate() + (7 * interval));
    } else if (frequency === "Monthly") {
        last_date.setMonth(last_date.getMonth() + interval);
    } else if (frequency === "Yearly") {
        last_date.setFullYear(last_date.getFullYear() + interval);
    }

    frm.set_value("custom__next_maintenance_date", frappe.datetime.obj_to_str(last_date));
}