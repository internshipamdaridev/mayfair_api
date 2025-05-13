from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


from mayfair_api.orders.models import CartItem, Order
from mayfair_api.orders.serializers import (
    CartItemSerializer,
    OrderSerializer,
    CreateOrderSerializer,
)

from mayfair_api.payments.models import Payment
from mayfair_api.payments.serializers import PaymentSerializer


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user).select_related("product")

    def perform_create(self, serializer):
        product = serializer.validated_data["product"]
        quantity = serializer.validated_data.get("quantity", 1)

        # Check if item already exists in cart
        cart_item, created = CartItem.objects.get_or_create(
            user=self.request.user, product=product, defaults={"quantity": quantity}
        )

        if not created:
            cart_item.quantity = quantity
            # cart_item.quantity += quantity
            cart_item.save()

    @action(detail=False, methods=["delete"])
    def clear(self, request):
        self.get_queryset().delete()
        return Response({"status": "cart cleared"}, status=status.HTTP_204_NO_CONTENT)


class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related("items")

    def get_serializer_class(self):
        if self.action == "create":
            return CreateOrderSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        # 1. Validate and create order with CreateOrderSerializer
        create_serializer = self.get_serializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        order = create_serializer.save()

        # 2. Get the payment instance
        payment = Payment.objects.get(order=order)

        # 3. Return both objects
        response_data = {
            "order": OrderSerializer(order).data,
            "payment": PaymentSerializer(payment).data,
        }

        headers = self.get_success_headers(OrderSerializer(order).data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status != "pending":
            return Response(
                {"error": "Only pending orders can be cancelled"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = "cancelled"
        order.save()
        return Response({"status": "order cancelled"})
