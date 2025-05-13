from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from mayfair_api.payments.models import Payment, PaymentMethod
from mayfair_api.payments.serializers import PaymentSerializer, PaymentMethodSerializer
from mayfair_api.payments.utils.paystack import PayStack
from mayfair_api.orders.serializers import OrderSerializer
from mayfair_api.orders.models import Order


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(order__user=self.request.user)

    @action(detail=False, methods=["post"])
    def verify(self, request):
        reference = request.data.get("reference")
        if not reference:
            return Response(
                {"error": "Reference is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Verify payment with Paystack
            paystack = PayStack()
            verified, data = paystack.confirm_transaction(reference)

            if verified:
                # Get the order associated with this payment
                try:
                    payment = Payment.objects.get(payment_reference=reference)
                    order = payment.order

                    # Update payment status
                    payment.status = "completed"
                    payment.transaction_id = data.get("id")
                    payment.save()

                    # Update order status
                    order.mark_as_paid(reference)
                    order.status = "processing"  # Move to next status
                    order.save()

                    return Response(
                        {
                            "status": "success",
                            "message": "Payment verified and order updated",
                            "order": OrderSerializer(order).data,
                            "payment": PaymentSerializer(payment).data,
                        }
                    )
                except Payment.DoesNotExist:
                    return Response(
                        {"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND
                    )
            else:
                return Response(
                    {"error": "Payment verification failed"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PaystackInitializePayment(APIView):
    paystack = PayStack()
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            # Get the order ID from request if you're paying for a specific order
            order_id = request.data.get("order_id")
            if order_id:
                try:
                    order = Order.objects.get(id=order_id, user=request.user)
                    amount = int(order.total_amount * 100)  # Convert to kobo
                    email = request.user.email
                except Order.DoesNotExist:
                    return Response(
                        {"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND
                    )
            else:
                # For cases where you're not paying for a specific order yet
                email = request.data.get("email")
                amount = request.data.get("amount")  # in kobo

            response, message = self.paystack.initialize_transaction(
                email,
                amount=amount,
                metadata={"user_id": request.user.id, "order_id": order_id},
            )

            if response:
                return Response(message, status=status.HTTP_200_OK)
            return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PaystackConfirmPayment(APIView):
    paystack = PayStack()
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, reference):
        print("using this")
        try:
            verified, message = self.paystack.confirm_transaction(reference)

            if verified:
                print("using this....")

                # Find or create payment record
                try:
                    payment = Payment.objects.get(payment_reference=reference)
                except Payment.DoesNotExist:
                    # If payment record doesn't exist, create one
                    # This might happen if the payment was initiated outside our system
                    metadata = message.get("metadata", {})
                    order_id = metadata.get("order_id")

                    if not order_id:
                        return Response(
                            {"error": "Order reference not found in payment data"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    try:
                        order = Order.objects.get(id=order_id, user=request.user)
                    except Order.DoesNotExist:
                        return Response(
                            {"error": "Order not found"},
                            status=status.HTTP_404_NOT_FOUND,
                        )

                    payment = Payment.objects.create(
                        order=order,
                        payment_method="credit_card",  # Default for Paystack
                        amount=message["amount"] / 100,  # Convert from kobo
                        status="completed",
                        transaction_id=message["id"],
                        payment_reference=reference,
                    )

                # Update payment and order status
                payment.status = "completed"
                payment.transaction_id = message.get("id")
                payment.save()

                order = payment.order
                order.mark_as_paid(reference)
                order.status = "processing"
                order.save()
                print("using this....saved")

                return Response(
                    {
                        "message": "Payment verified successfully",
                        "order": OrderSerializer(order).data,
                        "payment": PaymentSerializer(payment).data,
                    },
                    status=status.HTTP_200_OK,
                )
            return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # class PaystackInitializePayment(APIView):
    #     paystack = PayStack()

    #     def post(self, request):
    #         try:
    #             email = request.data.get("email")
    #             amount = request.data.get("amount")  # in kobo

    #             response, message = self.paystack.initialize_transaction(
    #                 email, amount=amount
    #             )
    #             if response:

    #                 return Response(message, status=status.HTTP_200_OK)
    #             return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)

    #         except Exception as e:
    #             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # class PaystackConfirmPayment(APIView):
    paystack = PayStack()

    def get(self, request, reference):
        try:
            verified, message = self.paystack.confirm_transaction(reference)
            print("Now verified", verified)
            if verified:
                return Response(
                    {
                        "message": message,
                    },
                    status=status.HTTP_200_OK,
                )
            return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(order__customer=self.request.user)


class PaymentDetailView(generics.RetrieveAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(order__customer=self.request.user)


class PaymentMethodListView(generics.ListAPIView):
    queryset = PaymentMethod.objects.filter(is_active=True)
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.AllowAny]
