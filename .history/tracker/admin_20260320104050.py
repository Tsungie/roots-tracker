from django.contrib import admin
from .models import Member, Meeting, Attendance, Payment

admin.site.register(Member)
admin.site.register(Meeting)
admin.site.register(Attendance)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("member", "month", "year", "status", "uploaded_at")
    list_filter = ("status", "month", "year")
    search_fields = ("member__first_name", "member__last_name")
