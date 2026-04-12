frappe.ui.form.on('Accommodation Assignment', {
    refresh(frm) {
        set_room_options(frm);
    },

    accommodation(frm) {
        frm.set_value('room_number', '');
        set_room_options(frm);
    }
});

function set_room_options(frm) {
    if (!frm.doc.accommodation) {
        frm.set_df_property('room_number', 'options', ['']);
        return;
    }

    frappe.db.get_doc('Accommodation', frm.doc.accommodation).then(doc => {
        let room_options = [''];

        if (doc.rooms && doc.rooms.length) {
            doc.rooms.forEach(row => {
                if (row.room_number) {
                    room_options.push(row.room_number);
                }
            });
        }

        frm.set_df_property('room_number', 'options', room_options);
    });
}