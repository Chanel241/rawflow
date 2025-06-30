from django.urls import path
from . import views

app_name = 'traceability'

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add/', views.add_transaction, name='add_transaction'),
    path('search/', views.search, name='search_results'),  # Changé search_results en search
    path('export-pdf/', views.export_pdf, name='export_pdf'),
]