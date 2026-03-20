from django import forms
from .models import Payment


class ReceiptUploadForm(forms.ModelForm):
    class Meta:
        model = Payment
        # Add 'payment_method' to the list of fields
        fields = ["member", "month", "payment_method", "receipt_image"]

        widgets = {
            "member": forms.Select(
                attrs={"style": "width: 100%; padding: 10px; margin-bottom: 15px;"}
            ),
            "month": forms.Select(
                attrs={"style": "width: 100%; padding: 10px; margin-bottom: 15px;"}
            ),
            # Add styling for the new dropdown
            "payment_method": forms.Select(
                attrs={"style": "width: 100%; padding: 10px; margin-bottom: 15px;"}
            ),
            "receipt_image": forms.FileInput(attrs={"style": "margin-bottom: 15px;"}),
        }
