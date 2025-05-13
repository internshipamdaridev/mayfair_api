from django.urls import path, include
from rest_framework.routers import DefaultRouter


from .views import (
    PaymentViewSet,
    PaymentListView,
    PaymentDetailView,
    PaymentMethodListView,
    PaystackInitializePayment,
    PaystackConfirmPayment,
)

router = DefaultRouter()

router.register(r"payments", PaymentViewSet, basename="payment")

urlpatterns = [
    path(
        "initialize-payment/",
        PaystackInitializePayment.as_view(),
        name="initialize-payment",
    ),
    path(
        "confirm-payment/<str:reference>/",
        PaystackConfirmPayment.as_view(),
        name="confirm-payment",
    ),
    path("payments/", PaymentListView.as_view(), name="payment-list"),
    path("payments/<int:pk>/", PaymentDetailView.as_view(), name="payment-detail"),
    path("payment-methods/", PaymentMethodListView.as_view(), name="payment-methods"),
]
