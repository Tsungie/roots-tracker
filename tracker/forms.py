from django import forms
from .models import Payment, Attendance


class ReceiptUploadForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["member", "amount", "month", "year", "payment_method", "transaction_id", "receipt_image", "status", "admin_notes", "receipt_file"]

        widgets = {
            "member": forms.Select(attrs={"class": "form-control"}),
            "amount": forms.NumberInput(attrs={"class": "form-control"}),
            "month": forms.Select(attrs={"class": "form-control"}),
            "year": forms.NumberInput(attrs={"class": "form-control"}),
            "payment_method": forms.Select(attrs={"class": "form-control"}),
            "transaction_id": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. TXN123456 or bank reference number",
            }),
            "receipt_image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "admin_notes": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. paid through Stanbic",
            }),
            "receipt_file": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ["mode", "comments"]
        widgets = {
            "mode": forms.Select(attrs={"class": "form-select"}),
            "comments": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Optional notes"}
            ),
        }
