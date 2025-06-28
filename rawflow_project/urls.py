from django.contrib import admin
from django.urls import path, include
from traceability.views import CustomSignupView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api_urls')),
    path('accounts/signup/', CustomSignupView.as_view(), name='account_signup'),
    path('accounts/', include('allauth.urls')),
    path('', include('traceability.urls')),
    path('export-pdf/', views.export_pdf, name='export_pdf'),
]