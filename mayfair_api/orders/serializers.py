from decimal import Decimal
from django.db import transaction
from rest_framework import serializers


from mayfair_api.products.serializers import ProductSerializer
from mayfair_api.products.models import Product
from mayfair_api.orders.models import Order, OrderItem, CartItem, ShippingMethod
from mayfair_api.payments.models import Payment


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product", write_only=True
    )

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product",
            "product_id",
            "quantity",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "user"]

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1")
        return value


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity", "price", "total_price"]
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    payment_method_display = serializers.CharField(
        source="get_payment_method_display", read_only=True
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "status",
            "status_display",
            "payment_method",
            "payment_method_display",
            "total_amount",
            "created_at",
            "updated_at",
            "items",
        ]
        read_only_fields = [
            "id",
            "order_number",
            "total_amount",
            "created_at",
            "updated_at",
            "items",
        ]


class CreateOrderSerializer(serializers.Serializer):
    payment_method = serializers.ChoiceField(choices=Order.PAYMENT_METHODS)
    # email = serializers.EmailField(required=True)  # For payment processing

    def validate(self, attrs):
        user = self.context["request"].user
        if not CartItem.objects.filter(user=user).exists():
            raise serializers.ValidationError("Your cart is empty")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user
        cart_items = CartItem.objects.filter(user=user).select_related("product")

        # TODO: update calculations
        subtotal = sum(item.total_price for item in cart_items)
        tax = subtotal * Decimal("0.10")  # 10% tax
        shipping_cost = Decimal("5.00")
        total_amount = subtotal + tax + shipping_cost

        order = Order.objects.create(
            user=user,
            payment_method=validated_data["payment_method"],
            subtotal=subtotal,
            tax=tax,
            shipping_cost=shipping_cost,
            total_amount=total_amount,
            shipping_address=user.customer_profile.shipping_address,
            billing_address=user.customer_profile.billing_address,
        )

        OrderItem.objects.bulk_create(
            [
                OrderItem(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price,
                )
                for item in cart_items
            ]
        )

        Payment.objects.create(
            order=order,
            payment_method=validated_data["payment_method"],
            amount=total_amount,
            status="pending",
        )

        cart_items.delete()
        return order


class ShippingMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingMethod
        fields = "__all__"
