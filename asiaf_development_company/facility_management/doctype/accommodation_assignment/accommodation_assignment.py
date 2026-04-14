import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, getdate


class AccommodationAssignment(Document):
    def validate(self):
        self.validate_assignment_status_logic()
        self.validate_date_order()
        self.validate_room_number_belongs_to_accommodation()
        self.validate_accommodation_status_for_active_assignment()
        self.validate_room_status_for_active_assignment()
        self.validate_room_capacity_for_active_assignment()

    def on_update(self):
        self.refresh_linked_room_occupancy()

    def on_trash(self):
        self.refresh_linked_room_occupancy(exclude_current=True)

    def validate_assignment_status_logic(self):
        status = (self.assignment_status or "").strip()

        if status == "Checked Out" and not self.actual_check_out_date:
            frappe.throw(
                _("Actual Check Out Date is required when Assignment Status is Checked Out.")
            )

        if status in ["Planned", "Active", "Cancelled"] and self.actual_check_out_date:
            frappe.throw(
                _("Actual Check Out Date should only be filled when Assignment Status is Checked Out.")
            )

    def validate_date_order(self):
        if self.check_in_date and self.expected_check_out_date:
            if getdate(self.expected_check_out_date) < getdate(self.check_in_date):
                frappe.throw(
                    _("Expected Check Out Date cannot be before Check In Date.")
                )

        if self.check_in_date and self.actual_check_out_date:
            if getdate(self.actual_check_out_date) < getdate(self.check_in_date):
                frappe.throw(
                    _("Actual Check Out Date cannot be before Check In Date.")
                )

    def validate_room_number_belongs_to_accommodation(self):
        if not self.accommodation or not self.room_number:
            return

        accommodation = frappe.get_doc("Accommodation", self.accommodation)
        valid_room_numbers = [row.room_number for row in accommodation.rooms if row.room_number]

        if str(self.room_number) not in [str(r) for r in valid_room_numbers]:
            frappe.throw(
                _("Room Number {0} does not exist in Accommodation {1}.").format(
                    self.room_number, self.accommodation
                )
            )

    def validate_accommodation_status_for_active_assignment(self):
        if self.assignment_status != "Active":
            return

        if not self.accommodation:
            return

        accommodation = frappe.get_doc("Accommodation", self.accommodation)

        if accommodation.status in ["Inactive", "Under Maintenance"]:
            frappe.throw(
                _("You cannot create an Active assignment because Accommodation {0} is {1}.").format(
                    self.accommodation, accommodation.status
                )
            )

    def validate_room_status_for_active_assignment(self):
        if self.assignment_status != "Active":
            return

        if not self.accommodation or not self.room_number:
            return

        accommodation = frappe.get_doc("Accommodation", self.accommodation)

        selected_room = None
        for room in accommodation.rooms:
            if str(room.room_number) == str(self.room_number):
                selected_room = room
                break

        if not selected_room:
            return

        if selected_room.room_status in ["Blocked", "Under Maintenance"]:
            frappe.throw(
                _("You cannot create an Active assignment because Room Number {0} is {1}.").format(
                    self.room_number, selected_room.room_status
                )
            )

    def validate_room_capacity_for_active_assignment(self):
        if not self.accommodation or not self.room_number:
            return

        if self.assignment_status != "Active":
            return

        accommodation = frappe.get_doc("Accommodation", self.accommodation)

        selected_room = None
        for room in accommodation.rooms:
            if str(room.room_number) == str(self.room_number):
                selected_room = room
                break

        if not selected_room:
            return

        number_of_beds = cint(selected_room.number_of_beds or 0)

        if number_of_beds <= 0:
            frappe.throw(
                _("Room Number {0} has no valid Number of Beds.").format(self.room_number)
            )

        filters = {
            "accommodation": self.accommodation,
            "room_number": self.room_number,
            "assignment_status": "Active"
        }

        if not self.is_new():
            filters["name"] = ["!=", self.name]

        current_active_count = frappe.db.count("Accommodation Assignment", filters)

        if current_active_count >= number_of_beds:
            frappe.throw(
                _("Room Number {0} is already full. Number of Beds: {1}, Current Occupancy: {2}.").format(
                    self.room_number, number_of_beds, current_active_count
                )
            )

    def refresh_linked_room_occupancy(self, exclude_current=False):
        rooms_to_refresh = set()

        if self.accommodation and self.room_number:
            rooms_to_refresh.add((self.accommodation, str(self.room_number)))

        previous_doc = self.get_doc_before_save()
        if previous_doc and previous_doc.accommodation and previous_doc.room_number:
            rooms_to_refresh.add((previous_doc.accommodation, str(previous_doc.room_number)))

        for accommodation_name, room_number in rooms_to_refresh:
            update_room_occupancy_and_status(
                accommodation_name=accommodation_name,
                room_number=room_number,
                exclude_assignment=self.name if exclude_current else None
            )


def update_room_occupancy_and_status(accommodation_name, room_number, exclude_assignment=None):
    filters = {
        "accommodation": accommodation_name,
        "room_number": room_number,
        "assignment_status": "Active"
    }

    if exclude_assignment:
        filters["name"] = ["!=", exclude_assignment]

    active_assignments = frappe.get_all(
        "Accommodation Assignment",
        filters=filters,
        fields=["name"]
    )

    current_occupancy = len(active_assignments)

    accommodation = frappe.get_doc("Accommodation", accommodation_name)
    room_found = False
    changed = False

    for room in accommodation.rooms:
        if str(room.room_number) != str(room_number):
            continue

        room_found = True

        if cint(room.current_occupancy or 0) != current_occupancy:
            room.current_occupancy = current_occupancy
            changed = True

        auto_status = get_auto_room_status(
            current_status=room.room_status,
            number_of_beds=cint(room.number_of_beds or 0),
            current_occupancy=current_occupancy
        )

        if auto_status and room.room_status != auto_status:
            room.room_status = auto_status
            changed = True

        break

    if room_found and changed:
        accommodation.save(ignore_permissions=True)


def get_auto_room_status(current_status, number_of_beds, current_occupancy):
    if current_status in ["Blocked", "Under Maintenance"]:
        return None

    if current_occupancy <= 0:
        return "Available"

    if number_of_beds > 0 and current_occupancy < number_of_beds:
        return "Partially Occupied"

    return "Occupied"