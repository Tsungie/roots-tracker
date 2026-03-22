from django.contrib import admin
from .models import (
    Group,
    Member,
    Meeting,
    Attendance,
    Payment,
    WhatsAppDraft,
    Topic)
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from django.db.models import Sum
import io

# Removed 'Dashboard' from here since we deleted the fake model
from .models import Member, Meeting, Attendance, Payment

# ==========================================
# 1. THE PDF GENERATOR SCRIPTS (ACTIONS)
# ==========================================


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("title", "group", "order")
    list_filter = ("group",)
    ordering = ("group", "order")


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

    if queryset.count() == 1:
        person = queryset.first()
        filename = f"Roots_{person.first_name}_{person.last_name}_Summary.pdf"
    else:
        filename = "Roots_Group_Summary.pdf"

    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    response.write(pdf)
    return response


# ==========================================
# 2. REGISTER STANDARD MODELS
# ==========================================

admin.site.register(Meeting)
admin.site.register(Attendance)
admin.site.register(Group)
admin.site.register(Member)
admin.site.register(Meeting)
admin.site.register(Attendance)
admin.site.register(Payment)
admin.site.register(WhatsAppDraft)


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


# ==========================================
# 4. THE HOMEPAGE DASHBOARD HIJACK
# ==========================================
# Notice how this is completely pushed to the left wall (no indentation)
original_admin_index = admin.site.index


def roots_admin_index(request, extra_context=None):
    # Everything inside the function gets indented exactly 4 spaces
    extra_context = extra_context or {}

    total_approved = (
        Payment.objects.filter(status="approved").aggregate(Sum("amount"))[
            "amount__sum"
        ]
        or 0
    )
    extra_context["total_approved"] = total_approved
    extra_context["pending_count"] = Payment.objects.filter(status="pending").count()
    extra_context["member_count"] = Member.objects.count()

    extra_context["members_list"] = Member.objects.all().order_by("first_name")

    admin.site.index_template = "tracker/admin_dashboard.html"

    return original_admin_index(request, extra_context=extra_context)


admin.site.index = roots_admin_index
