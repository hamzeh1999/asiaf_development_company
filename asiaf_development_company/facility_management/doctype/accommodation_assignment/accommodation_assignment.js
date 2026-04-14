frappe.ui.form.on('Accommodation Assignment', {
    refresh(frm) {
        set_room_options(frm);
        update_room_details(frm);
    },

    accommodation(frm) {
        frm.set_value('room_number', '');
        frm.set_value('room_details', '');
        set_room_options(frm);
    },

    room_number(frm) {
        update_room_details(frm);
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
                    room_options.push(String(row.room_number));
                }
            });
        }

        frm.set_df_property('room_number', 'options', room_options);
    });
}

function update_room_details(frm) {
    if (!frm.doc.accommodation || !frm.doc.room_number) {
        frm.set_value('room_details', '');
        return;
    }

    frappe.db.get_doc('Accommodation', frm.doc.accommodation).then(doc => {
        if (!doc.rooms || !doc.rooms.length) {
            frm.set_value('room_details', '');
            return;
        }

        let selected_room = doc.rooms.find(row =>
            String(row.room_number) === String(frm.doc.room_number)
        );

        if (!selected_room) {
            frm.set_value('room_details', '');
            return;
        }

        let details = [
            `Floor Number: ${selected_room.floor_number || ''}`,
            `Room Type: ${selected_room.room_type || ''}`,
            `Number of Beds: ${selected_room.number_of_beds || ''}`,
            `Current Occupancy: ${selected_room.current_occupancy || ''}`,
            `Room Status: ${selected_room.room_status || ''}`,
            `Allowed Occupant Group: ${selected_room.allowed_occupant_group || ''}`
        ].join('\n');

        frm.set_value('room_details', details);
    });
}