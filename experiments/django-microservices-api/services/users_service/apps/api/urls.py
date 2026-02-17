from django.urls import path

from .views import HealthView, UserListView

urlpatterns = [
    path('health/', HealthView.as_view(), name='health'),
    path('users/', UserListView.as_view(), name='users'),
]
