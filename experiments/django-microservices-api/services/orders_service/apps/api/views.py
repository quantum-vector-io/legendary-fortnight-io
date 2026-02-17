from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order


class HealthView(APIView):
    def get(self, request):
        return Response({'status': 'ok', 'service': 'orders'})


class OrderListView(APIView):
    def get(self, request):
        orders = Order.objects.all().values('id', 'user_id', 'amount', 'currency', 'status', 'created_at')
        return Response(list(orders))

    def post(self, request):
        order = Order.objects.create(
            user_id=request.data['user_id'],
            amount=request.data['amount'],
            currency=request.data.get('currency', 'USD'),
        )
        return Response({'id': order.id, 'status': order.status}, status=201)
