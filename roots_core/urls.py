from django.contrib import admin
from django.urls import path
from tracker import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    # 1. The Lobby (Homepage)
    path("", views.select_group, name="select_group"),
    # 2. The Group Command Center
    path("dashboard/", views.dashboard, name="dashboard"),
    path("export-pdf/", views.export_status_pdf, name="export_pdf"),
    # 3. The Bulk Upload Tool
    path("upload/", views.upload_receipt, name="upload_receipt"),
    path("success/", views.upload_success, name="upload_success"),
    # 4. Reports & Webhooks
    path("download-summary/", views.download_summary_summary, name="download_summary"),
    path("export/pdf/", views.export_status_pdf, name="export_pdf"),
    path("export/word/", views.export_status_word, name="export_word"),
    path("meeting/<int:meeting_id>/", views.meeting_detail, name="meeting_detail"),
    path("member/add/", views.manage_member, name="add_member"),
    path("member/edit/<int:member_id>/", views.manage_member, name="edit_member"),
    path("member/<int:member_id>/", views.member_detail, name="member_detail"),
    path("whatsapp/webhook/", views.whatsapp_webhook, name="whatsapp_webhook"),
    path("attendance/", views.mark_attendance, name="mark_attendance"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
