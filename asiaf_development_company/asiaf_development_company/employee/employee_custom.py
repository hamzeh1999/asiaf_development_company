import frappe
from frappe.utils import getdate, date_diff

def validate_employee_id(doc, method):
    # التأكد أن الحساب فقط للمقيمين
    if doc.citizenship_status in ['Non-Saudi', 'Son of Saudi Mother'] and doc.iqama_expiry_date:
        today = getdate()
        days_left = date_diff(doc.iqama_expiry_date, today)
        
        # تخزين الأيام المتبقية في الحقل المخصص
        # ملاحظة: تأكد أنك أنشأت الحقل 'days_remaining_for_iqama' في Customize Form
        doc.days_remaining_for_iqama = days_left
        
        # تحديد الحالة
        if days_left < 0:
            doc.id_status = "Expired (منتهية)"
        elif days_left < 30:
            doc.id_status = "Expiring Soon (توشك على الانتهاء)"
        else:
            doc.id_status = "Valid (سارية)"