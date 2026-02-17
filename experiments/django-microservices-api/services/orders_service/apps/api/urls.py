from django.urls import path

from .views import HealthView, OrderListView

urlpatterns = [
    path('health/', HealthView.as_view(), name='health'),
    path('orders/', OrderListView.as_view(), name='orders'),
]
