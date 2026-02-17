from django.db import models


class Order(models.Model):
    user_id = models.IntegerField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=32, default='created')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f'Order<{self.id}>:{self.status}'
