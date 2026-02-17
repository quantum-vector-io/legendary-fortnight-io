from rest_framework.response import Response
from rest_framework.views import APIView

from .models import UserProfile


class HealthView(APIView):
    def get(self, request):
        return Response({'status': 'ok', 'service': 'users'})


class UserListView(APIView):
    def get(self, request):
        users = UserProfile.objects.all().values('id', 'email', 'full_name', 'created_at')
        return Response(list(users))

    def post(self, request):
        user = UserProfile.objects.create(
            email=request.data['email'],
            full_name=request.data['full_name'],
        )
        return Response({'id': user.id, 'email': user.email, 'full_name': user.full_name}, status=201)
