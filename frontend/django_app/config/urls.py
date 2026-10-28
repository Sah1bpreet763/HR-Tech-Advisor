from django.contrib import admin
from django.urls import path, include
from dashboard.views import landing_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('', landing_view, name='landing'),
]
