from django import forms
from .models import Payment


class ReceiptUploadForm(forms.ModelForm):
    class Meta:
        model = Payment
        # We only ask for the essentials. Amount, year, and status are handled automatically!
        fields = ["member", "month", "receipt_image"]

        # Adding some basic CSS classes so it looks nice on mobile later
        widgets = {
            "member": forms.Select(
                attrs={"style": "width: 100%; padding: 10px; margin-bottom: 15px;"}
            ),
            "month": forms.Select(
                attrs={"style": "width: 100%; padding: 10px; margin-bottom: 15px;"}
            ),
            "receipt_image": forms.FileInput(attrs={"style": "margin-bottom: 15px;"}),
        }
