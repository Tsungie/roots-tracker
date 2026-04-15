from django.contrib import admin
from .models import Group, Member, Meeting, Attendance, Payment, WhatsAppDraft, Topic
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
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
    # ... (Keep your existing export_to_pdf code here) ...
    pass


@admin.action(description="Download Member Summary Report")
def export_member_summary_pdf(modeladmin, request, queryset):
    # ... (Keep your existing export_member_summary_pdf code here) ...
    pass


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
        "amount",
        "payment_method",
        "transaction_id",
        "status",
        "uploaded_at",
    )
    list_filter = ("status", "month", "year", "payment_method")
    search_fields = ("member__first_name", "member__last_name", "transaction_id")
    actions = [export_to_pdf]


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
