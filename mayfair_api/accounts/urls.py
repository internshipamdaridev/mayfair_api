from django.urls import path, include
from rest_framework.routers import DefaultRouter

from djoser.views import UserViewSet

from mayfair_api.accounts import views

router = DefaultRouter()
router.register("accounts", views.CustomUserViewSet)
# router.register(r"vendor-profile", views.VendorProfileView, basename="vendor-profile")
#

urlpatterns = [
    path("", include(router.urls)),
    path("login/", views.MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("vendor-profile/", views.VendorProfileView.as_view(), name="vendor-profile"),
    # path("vendor-profile/", views.VendorProfileView.as_view(), name="vendor-profile"),
    path(
        "customer-profile/",
        views.CustomerProfileView.as_view(),
        name="customer-profile",
    ),
    path("auth/", include("rest_framework_social_oauth2.urls")),
    path("social/google/", include("social_django.urls", namespace="social")),
    path("auth/google/", views.google_auth_token, name="google_auth"),
    # path("auth/google/", views.google_login, name="google_auth"),
]
