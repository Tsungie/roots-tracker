from django.contrib import admin
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import io

from .models import Member, Meeting, Attendance, Payment


# --- THE PDF GENERATOR SCRIPT ---
@admin.action(description="Download PDF Report for selected payments")
def export_to_pdf(modeladmin, request, queryset):
    # Create a temporary memory buffer to hold the PDF data
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Add a title to the document
    styles = getSampleStyleSheet()
    title = Paragraph("Roots Monthly Payments Report", styles["Title"])
    elements.append(title)

    # Create the table headers
    data = [["Member Name", "Month", "Method", "Status", "Date Uploaded"]]

    # Loop through the selected records and add them as rows
    for payment in queryset:
        data.append(
            [
                str(payment.member),
                payment.get_month_display(),
                payment.get_payment_method_display(),
                payment.get_status_display().upper(),
                payment.uploaded_at.strftime("%Y-%m-%d"),
            ]
        )

    # Style the table to look professional
    t = Table(data)
    t.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#2c3e50"),
                ),  # Dark blue header
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                (
                    "BACKGROUND",
                    (0, 1),
                    (-1, -1),
                    colors.HexColor("#ecf0f1"),
                ),  # Light grey rows
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    elements.append(t)
    doc.build(elements)

    # Grab the completed PDF from the buffer and send it to the browser
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="roots_payment_report.pdf"'
    response.write(pdf)

    return response


# --------------------------------

# Register the standard models
admin.site.register(Member)
admin.site.register(Meeting)
admin.site.register(Attendance)


# Register the Payment model and attach our new PDF tool
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "member",
        "month",
        "year",
        "payment_method",
        "status",
        "uploaded_at",
    )
    list_filter = ("status", "month", "year", "payment_method")
    search_fields = ("member__first_name", "member__last_name")

    # This line adds the dropdown option!
    actions = [export_to_pdf]
