from django.urls import path
from . import views

app_name = 'traceability'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add/', views.add_transaction, name='add_transaction'),
    path('search/', views.search, name='search_results'),
]