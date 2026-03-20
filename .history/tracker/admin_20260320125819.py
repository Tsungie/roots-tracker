from django.contrib import admin
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import io

from .models import Member, Meeting, Attendance, Payment
from django.db.models import Sum

# ==========================================
# 1. THE PDF GENERATOR SCRIPTS (ACTIONS)
# ==========================================


@admin.action(description="Download PDF Report for selected payments")
def export_to_pdf(modeladmin, request, queryset):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    title = Paragraph("Roots Monthly Payments Report", styles["Title"])
    elements.append(title)

    data = [["Member Name", "Month", "Method", "Status", "Date Uploaded"]]

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

    t = Table(data)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ecf0f1")),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    elements.append(t)
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="roots_payment_report.pdf"'
    response.write(pdf)

    return response


@admin.action(description="Download Member Summary Report")
def export_member_summary_pdf(modeladmin, request, queryset):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    title = Paragraph("Roots Master Summary Report", styles["Title"])
    elements.append(title)

    data = [["Member Name", "Total Paid (Approved)", "Meetings Attended"]]

    for member in queryset:
        data.append(
            [
                f"{member.first_name} {member.last_name}",
                f"${member.total_approved_payments}",
                str(member.total_attendance),
            ]
        )

    t = Table(data)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8e44ad")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ecf0f1")),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    elements.append(t)
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")

    # --- UPDATE THIS BLOCK ---
    if queryset.count() == 1:
        # If you selected just one person, use their name!
        person = queryset.first()
        filename = f"Roots_{person.first_name}_{person.last_name}_Summary.pdf"
    else:
        # If you selected multiple people, use a general group name
        filename = "Roots_Group_Summary.pdf"

    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    # -------------------------

    response.write(pdf)
    return response


# ==========================================
# 2. REGISTER STANDARD MODELS
# ==========================================
# Notice Member is removed from here because we register it with the custom class below!
admin.site.register(Meeting)
admin.site.register(Attendance)


# ==========================================
# 3. CUSTOM ADMIN DASHBOARDS
# ==========================================


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "phone_number",
        "total_approved_payments",
        "total_attendance",
    )
    search_fields = ("first_name", "last_name")
    actions = [export_member_summary_pdf]


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
    actions = [export_to_pdf]
