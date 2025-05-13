from datetime import timezone
import time
from django.db import models
from django.core.validators import MinValueValidator

from mayfair_api.accounts.models import User
from mayfair_api.products.models import Product


class Order(models.Model):
    ORDER_STATUS_CHOICES = (
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
    )

    PAYMENT_METHODS = [
        ("credit_card", "Credit Card"),
        ("paypal", "PayPal"),
        ("bank_transfer", "Bank Transfer"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(
        max_length=20, choices=ORDER_STATUS_CHOICES, default="pending"
    )
    shipping_address = models.TextField()
    billing_address = models.TextField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    subtotal = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    tax = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0.00
    )
    shipping_cost = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0.00
    )
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    notes = models.TextField(blank=True)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.order_number} - {self.user.email}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"ORD-{self.user.id}-{int(time.time())}"
        super().save(*args, **kwargs)

    def mark_as_paid(self, reference):
        self.is_paid = True
        self.paid_at = timezone.now()
        self.payment_reference = reference
        self.save()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    discount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    # total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.quantity} x {self.product.name} (Order #{self.order.order_number})"
        )

    @property
    def total_price(self):
        return self.price * self.quantity


class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "product")  # Ensures one product per user in cart

    def __str__(self):
        return f"{self.quantity} x {self.product.name} ({self.user.email})"

    @property
    def total_price(self):
        return self.product.price * self.quantity


class ShippingMethod(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    estimated_delivery_time = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class AnonymousCart(models.Model):
    session_key = models.CharField(max_length=40, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AnonymousCartItem(models.Model):
    cart = models.ForeignKey(
        AnonymousCart, related_name="items", on_delete=models.CASCADE
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
