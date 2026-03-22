from django.contrib import admin
from django.urls import path
from tracker import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.select_group, name="select_group"),
    path("", views.upload_receipt, name="upload_receipt"),  # The main upload link
    path("success/", views.upload_success, name="upload_success"),
    path("whatsapp/webhook/", views.whatsapp_webhook, name="whatsapp_webhook"),
    path('download-summary/', views.download_master_summary, name='download_summary'),
    path('whatsapp/webhook/', views.whatsapp_webhook, name='whatsapp_webhook'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
