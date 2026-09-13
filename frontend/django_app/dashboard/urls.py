from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("audit/", views.questionnaire_view, name="questionnaire"),
    path("audit/results/<int:audit_id>/", views.audit_results_view, name="audit_results"),
    path("audit/history/", views.audit_history_view, name="audit_history"),
    path("audit/pdf/<int:audit_id>/", views.audit_pdf_download_view, name="audit_pdf"),
]

