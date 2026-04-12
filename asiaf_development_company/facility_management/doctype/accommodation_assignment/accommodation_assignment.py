import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class AccommodationAssignment(Document):
    def validate(self):
        self.validate_assignment_status_logic()
        self.validate_date_order()
        self.validate_room_number_belongs_to_accommodation()

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