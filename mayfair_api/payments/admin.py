from django.contrib import admin

from mayfair_api.payments.models import Payment, PaymentMethod

# Register your models here.


admin.site.register(Payment)
admin.site.register(PaymentMethod)
