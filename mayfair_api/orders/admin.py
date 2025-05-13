from django.contrib import admin

from mayfair_api.orders.models import CartItem, Order, OrderItem

# Register your models here.

admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(CartItem)
