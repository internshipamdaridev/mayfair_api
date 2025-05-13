import time
from django.db import models

from mayfair_api.orders.models import Order


class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    )

    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="payment"
    )
    payment_method = models.CharField(max_length=20, choices=Order.PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending"
    )
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_reference = models.CharField(max_length=100, unique=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment for Order #{self.order.order_number}"

    def save(self, *args, **kwargs):
        if not self.payment_reference:
            self.payment_reference = f"PAY-{self.order.user.id}-{int(time.time())}"
        super().save(*args, **kwargs)


class PaymentMethod(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    additional_info = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.name
