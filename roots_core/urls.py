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
    # 3. The Bulk Upload Tool
    path("upload/", views.upload_receipt, name="upload_receipt"),
    path("success/", views.upload_success, name="upload_success"),
    # 4. Reports & Webhooks
    path("download-summary/", views.download_summary_summary, name="download_summary"),
    path("whatsapp/webhook/", views.whatsapp_webhook, name="whatsapp_webhook"),
    path("attendance/", views.mark_attendance, name="mark_attendance"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
