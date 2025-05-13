from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CartViewSet,
    OrderViewSet,
)

router = DefaultRouter()
router.register(r"cart", CartViewSet, basename="cart")
router.register(r"", OrderViewSet, basename="order")


urlpatterns = [
    path("", include(router.urls)),
    # path("orders/", OrderViewSet.as_view(), name="order-list"),
    # path("carts/", CartViewSet.as_view(), name="order-list"),
    # path("orders/<str:order_number>/", OrderDetailView.as_view(), name="order-detail"),
    # path(
    #     "shipping-methods/", ShippingMethodListView.as_view(), name="shipping-methods"
    # ),
]
