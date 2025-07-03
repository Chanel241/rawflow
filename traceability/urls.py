from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

app_name = 'traceability'

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add_transaction/', views.add_transaction, name='add_transaction'),
    path('search/', views.search, name='search'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('export_pdf/', views.export_pdf, name='export_pdf'),
    # Inclure uniquement les URL d'allauth nécessaires (signup, logout, reset)
    path('accounts/signup/', views.CustomSignupView.as_view(), name='account_signup'),
    path('logout/', views.custom_logout, name='account_logout'),
    path('accounts/login/', views.custom_login, name='account_login'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='traceability/password_reset.html', success_url='/password_reset/done/'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='traceability/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='traceability/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='traceability/password_reset_complete.html'), name='password_reset_complete'),
]