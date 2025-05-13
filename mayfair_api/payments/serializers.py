from rest_framework import serializers


from mayfair_api.payments.models import Payment, PaymentMethod
from mayfair_api.orders.serializers import OrderSerializer


# serializers.py
class PaymentSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    payment_method_display = serializers.CharField(
        source="get_payment_method_display", read_only=True
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "order",
            "payment_method",
            "payment_method_display",
            "amount",
            "status",
            "status_display",
            "transaction_id",
            "payment_reference",
            "payment_date",
        ]
        read_only_fields = [
            "id",
            "status",
            "transaction_id",
            "payment_reference",
            "payment_date",
        ]


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = "__all__"
