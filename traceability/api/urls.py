from django.urls import path, include
from rest_framework.routers import DefaultRouter
from traceability.views import TransactionViewSet

router = DefaultRouter()
router.register(r'transactions', TransactionViewSet)

app_name = 'api'

urlpatterns = [
    path('', include(router.urls)),
]