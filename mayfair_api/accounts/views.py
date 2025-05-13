from django.core.exceptions import ValidationError

from djoser import signals
from djoser.views import UserViewSet
from djoser.compat import get_user_email
from djoser.conf import settings

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView


from rest_framework import generics, permissions, viewsets
from rest_framework.response import Response
from .models import VendorProfile, CustomerProfile
from .serializers import VendorProfileSerializer, CustomerProfileSerializer

from mayfair_api.accounts import serializers
from mayfair_api.accounts.permissions import IsVendorOwner


from rest_framework.decorators import api_view, permission_classes
from django.conf import settings as django_settings
from django.shortcuts import get_object_or_404
from google.oauth2 import id_token
from google.auth.transport import requests
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

import logging

logger = logging.getLogger(__name__)


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = serializers.MyTokenObtainPairSerializer


class CustomUserViewSet(UserViewSet):
    def get_serializer_class(self):
        if self.action == "create":
            return serializers.UserRegistrationSerializer
        elif self.action == "me" or self.action == "retrieve":
            return serializers.UserRetrieveSerializer
        return super().get_serializer_class()

    def create(self, request):
        print("CREATING USERP")
        try:
            serializer = serializers.UserRegistrationSerializer(data=request.data)
            print("data sent", request.data)
            serializer.is_valid(raise_exception=True)
            # self.perform_create(serializer)
            # return Response(serializer.data, status=status.HTTP_201_CREATED)

            user = self.perform_create(serializer)
            print(serializer)
            # Get user URL from serializer
            user_url = serializer.data["url"]
            if self.request.data["user_type"] == "customer":
                user_role = "customer"
            elif self.request.data["user_type"] == "vendor":
                user_role = "vendor"
            # Generate refresh and access tokens with user URL as custom claim
            refresh = RefreshToken.for_user(user)
            refresh["user_url"] = user_url
            refresh["user_role"] = user_role
            access = str(refresh.access_token)
            access_payload = refresh.access_token.payload
            access_payload["user_url"] = user_url
            access_payload["user_role"] = user_role
            refresh.access_token.payload = access_payload

            # Return response with tokens
            return Response(
                {"user": serializer.data, "refresh": str(refresh), "access": access},
                status=status.HTTP_201_CREATED,
            )

        except ValidationError as e:
            return Response({"error": e}, status=400)

    def perform_create(self, serializer):
        user = serializer.save()
        signals.user_registered.send(
            sender=self.__class__, user=user, request=self.request
        )

        context = {"user": user}
        to = [get_user_email(user)]
        if settings.SEND_ACTIVATION_EMAIL:
            settings.EMAIL.activation(self.request, context).send(to)
        elif settings.SEND_CONFIRMATION_EMAIL:
            settings.EMAIL.confirmation(self.request, context).send(to)

        return user

    # @action(detail=False, methods=["patch"], permission_classes=[IsAuthenticated])
    # def update_profile(self, request):
    #     user = request.user
    #     serializer = serializers.UserProfileUpdateSerializer(
    #         user, data=request.data, partial=True
    #     )

    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class VendorProfileView(generics.RetrieveUpdateAPIView):
#     serializer_class = VendorProfileSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def get_object(self):
#         return self.request.user.vendor_profile

#     def perform_update(self, serializer):
#         serializer.save(user=self.request.user)


class VendorProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = VendorProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        # Get the vendor profile for the current authenticated user
        return get_object_or_404(VendorProfile, user=self.request.user)

    def update(self, request, *args, **kwargs):
        # Block PUT requests - only allow PATCH
        if request.method == "PUT":
            return Response(
                {"detail": "Method not allowed. Use PATCH for partial updates."},
                status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )
        return super().update(request, *args, **kwargs)

    def perform_update(self, serializer):
        # Ensure the user field can't be changed
        serializer.save(user=self.request.user)


class CustomerProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = CustomerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.customer_profile

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


User = get_user_model()


@api_view(["POST"])
@permission_classes([AllowAny])
def google_login(request):
    """
    Verify Google token and create/login user
    """
    token = request.data.get("id_token")

    if not token:
        return Response(
            {"error": "ID token is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Verify the token
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), django_settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
        )

        # Check if issuer is Google
        if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
            return Response(
                {"error": "Wrong issuer"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Check if email is verified
        if not idinfo.get("email_verified", False):
            return Response(
                {"error": "Email not verified by Google"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get email and create unique username
        email = idinfo["email"]
        username = email  # Use email as username

        # Try to get existing user or create a new one
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = User.objects.create_user(
                # username=username,
                email=email,
                first_name=idinfo.get("given_name", ""),
                last_name=idinfo.get("family_name", ""),
                password=None,  # No password as they'll login with Google
            )

        # Create or get token
        token, _ = Token.objects.get_or_create(user=user)

        # Return user data and token
        return Response(
            {
                "token": token.key,
                "user_id": user.pk,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
        )

    except ValueError as e:
        # Invalid token
        return Response(
            {"error": f"Invalid token: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        # Other errors
        return Response(
            {"error": f"Authentication failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def google_auth_token(request):
    """
    Authenticate/register user with Google user info
    Returns a DRF auth token for authenticated users
    """
    try:
        # Check if we're getting ID token or user info
        if "id_token" in request.data:
            # Original flow using ID token (keep this for compatibility)
            id_token_value = request.data.get("id_token")

            # Verify token
            idinfo = id_token.verify_oauth2_token(
                id_token_value,
                requests.Request(),
                settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
            )

            # Check issuer
            if idinfo["iss"] not in [
                "accounts.google.com",
                "https://accounts.google.com",
            ]:
                return Response(
                    {"error": "Wrong issuer"}, status=status.HTTP_400_BAD_REQUEST
                )

            email = idinfo["email"]
            first_name = idinfo.get("given_name", "")
            last_name = idinfo.get("family_name", "")

        elif "google_user_info" in request.data:
            # New flow using user info directly
            user_info = request.data.get("google_user_info")

            if not user_info or "email" not in user_info:
                return Response(
                    {"error": "Invalid user info"}, status=status.HTTP_400_BAD_REQUEST
                )

            email = user_info["email"]
            first_name = user_info.get("given_name", "")
            last_name = user_info.get("family_name", "")
        else:
            return Response(
                {"error": "No valid authentication data provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get or create user
        try:
            user = User.objects.get(email=email)
            # Update user info if needed
            update_fields = []
            if not user.first_name and first_name:
                user.first_name = first_name
                update_fields.append("first_name")
            if not user.last_name and last_name:
                user.last_name = last_name
                update_fields.append("last_name")
            if update_fields:
                user.save(update_fields=update_fields)
        except User.DoesNotExist:
            # Create new user
            username = email
            user = User.objects.create_user(
                # username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                # Don't set password as they'll use Google to sign in
                password=None,  # No password as they'll login with Google
            )

        # Generate or retrieve token
        token, created = Token.objects.get_or_create(user=user)

        return Response(
            {
                "token": token.key,
                "user_id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
        )

    except ValueError as e:
        logger.error(f"Google authentication error: {e}")
        return Response(
            {"error": f"Invalid authentication: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.exception(f"Unexpected error in Google authentication: {e}")
        return Response(
            {"error": "Authentication failed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
