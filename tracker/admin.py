from django.contrib import admin
import zipfile
import urllib.request
from .models import Group, Member, Meeting, Attendance, Payment, WhatsAppDraft, Topic
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet
from django.db.models import Sum
import io

# ==========================================
# 1. TOPIC & MEETING REGISTRATION
# ==========================================


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("title", "group", "order")
    list_filter = ("group",)
    ordering = ("group", "order")


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ("topic", "date", "group")
    list_filter = ("group", "date")


# ==========================================
# 2. PDF ACTIONS
# ==========================================


@admin.action(description="Download PDF Report for selected payments")
def export_to_pdf(modeladmin, request, queryset):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    data = [["Member", "Month", "Year", "Amount", "Payment Date", "Status"]]
    for payment in queryset:
        data.append(
            [
                f"{payment.member.first_name} {payment.member.last_name}",
                payment.get_month_display(),
                str(payment.year),
                f"${payment.amount}",
                (
                    payment.payment_date.strftime("%d %b %Y")
                    if payment.payment_date
                    else "-"
                ),
                payment.status.upper(),
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
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    elements.append(t)
    doc.build(elements)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="payments_report.pdf"'
    return response


@admin.action(description="Download Member Summary Report")
def export_member_summary_pdf(modeladmin, request, queryset):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    data = [["Member", "Phone", "Total Paid", "Attendance"]]
    for member in queryset:
        data.append(
            [
                f"{member.first_name} {member.last_name}",
                member.phone_number,
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
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    elements.append(t)
    doc.build(elements)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="member_summary.pdf"'
    return response


@admin.action(description="📦 Download receipts as ZIP for selected payments")
def download_receipts_zip(modeladmin, request, queryset):
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w") as zip_file:
        for payment in queryset:
                   if payment.receipt_image:
                    try:
                        url = payment.receipt_image.url
                        # Handle local media files
                        if url.startswith('/media/'):
                            local_path = f"/home/misstsungie/roots-tracker{url}"
                            img = Image(local_path, width=4*inch, height=3*inch)
                        else:
                            # Cloudinary URL
                            with urllib.request.urlopen(url) as response:
                                img_data = io.BytesIO(response.read())
                            img = Image(img_data, width=4*inch, height=3*inch)
                        elements.append(img)
                    except Exception as e:
                        elements.append(Paragraph(f"(Could not load image: {e})", styles["Normal"]))

    buffer.seek(0)
    response = HttpResponse(buffer, content_type="application/zip")
    response["Content-Disposition"] = 'attachment; filename="receipts.zip"'
    return response


@admin.action(description="📄 Download receipts as PDF for selected payments")
def download_receipts_pdf(modeladmin, request, queryset):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    current_member = None

    for payment in queryset.order_by("member__first_name", "-year", "-month"):
        if current_member != payment.member:
            current_member = payment.member
            elements.append(Spacer(1, 12))
            elements.append(
                Paragraph(
                    f"{payment.member.first_name} {payment.member.last_name}",
                    styles["Heading1"],
                )
            )

        payment_date_str = (
            payment.payment_date.strftime("%d %b %Y")
            if payment.payment_date
            else "Date not recorded"
        )
        elements.append(
            Paragraph(
                f"{payment.get_month_display()} {payment.year} — ${payment.amount} via {payment.get_payment_method_display()} — Paid on {payment_date_str} — {payment.status.upper()}",
                styles["Normal"],
            )
        )

        if payment.receipt_image:
            try:
                url = payment.receipt_image.url
                with urllib.request.urlopen(url) as response:
                    img_data = io.BytesIO(response.read())
                img = Image(img_data, width=4 * inch, height=3 * inch)
                elements.append(img)
            except Exception as e:
                elements.append(
                    Paragraph(f"(Could not load image: {e})", styles["Normal"])
                )

        elements.append(Spacer(1, 12))

    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="receipts.pdf"'
    return response


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
        "get_month_year",
        "amount",
        "payment_method",
        "transaction_id",
        "status",
        "uploaded_at",
    )
    list_filter = ("status", "payment_method", "year", "month")
    search_fields = ("member__first_name", "member__last_name", "transaction_id")
    list_editable = ("status",)
    ordering = ("member__first_name", "member__last_name", "-year", "-month")
    actions = [export_to_pdf, download_receipts_zip, download_receipts_pdf]

    def get_month_year(self, obj):
        return f"{obj.get_month_display()} {obj.year}"

    get_month_year.short_description = "Period"


# ==========================================
# 4. REMAINING MODELS (REGISTER ONCE ONLY)
# ==========================================

admin.site.register(Attendance)
admin.site.register(Group)
admin.site.register(WhatsAppDraft)

# ==========================================
# 5. HOMEPAGE HIJACK
# ==========================================

original_admin_index = admin.site.index


def roots_admin_index(request, extra_context=None):
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
