from django.urls import path, include
from . import views

app_name = 'traceability'

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add_transaction/', views.add_transaction, name='add_transaction'),
    path('search/', views.search, name='search'),
    path('export_pdf/', views.export_pdf, name='export_pdf'),
    path('accounts/', include('allauth.urls')),
    path('logout/', views.custom_logout, name='account_logout'),  # Mise à jour pour utiliser la fonction custom_logout
]