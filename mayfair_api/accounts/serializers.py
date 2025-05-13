from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import VendorProfile, CustomerProfile
from djoser.serializers import UserCreateSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "user_type",
            "phone_number",
        ]


class UserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):

        model = User
        fields = [
            "email",
            "password",
            "first_name",
            "last_name",
            "user_type",
            "phone_number",
        ]

        extra_kwargs = {
            "password": {"write_only": True},
            "url": {"read_only": True},
        }

    # def create(self, validated_data):
    #     user = User.objects.create_user(
    #         email=validated_data["email"],
    #         password=validated_data["password"],
    #         first_name=validated_data.get("first_name", ""),
    #         last_name=validated_data.get("last_name", ""),
    #         user_type=validated_data.get("user_type", "customer"),
    #         phone_number=validated_data.get("phone_number", ""),
    #     )
    #     return user


# class VendorProfileSerializer(serializers.ModelSerializer):
#     user = UserSerializer(read_only=True)

#     class Meta:
#         model = VendorProfile
#         fields = "__all__"


class CustomerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = CustomerProfile
        fields = "__all__"


class UserRegistrationSerializer(UserCreateSerializer):
    profile = serializers.JSONField(write_only=True)

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            "id",
            "email",
            "password",
            "first_name",
            "last_name",
            "phone_number",
            "url",
            "user_type",
            "profile_picture",
            "profile",
        )

    def validate(self, attrs):
        profile_data = attrs.pop("profile", {})
        attrs = super().validate(attrs)
        attrs["profile"] = profile_data
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        profile_data = validated_data.pop("profile", {})
        user = super().create(validated_data)

        if user.user_type == "customer":
            # Create customer profile
            CustomerProfile.objects.create(user=user, **profile_data)

        else:
            # Create vendor profile as before
            VendorProfile.objects.create(user=user, **profile_data)

        return user


class UserRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "url",
            "user_type",
            "profile_picture",
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Check if the user is a customer
        if instance.user_type == "customer":
            print("User is a customer")

        if instance.user_type == "vendor":
            print("User is a vendor")
            try:
                vendor_profile = instance.vendor_profile
                representation["vendor_profile"] = VendorProfileSerializer(
                    vendor_profile
                ).data
            except Exception as e:
                print(f"Error getting vendor profile: {e}")
                pass

        return representation


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Call the parent class's validate method to get the token
        data = super().validate(attrs)

        # Add custom user data to the response
        user = self.user
        data["user"] = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "user_type": user.user_type,
            "url": user.url,
        }

        return data


class VendorProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = VendorProfile
        fields = [
            "id",
            "email",
            "phone_number",
            "business_name",
            "description",
            "line1",
            "line2",
            "city",
            "country",
            "zip_code",
            "contact_person",
            "logo",
            "tax_id",
            "kyc_verified",
            "kyc_document",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "kyc_verified"]
        extra_kwargs = {"kyc_document": {"write_only": True}}

    def update(self, instance, validated_data):
        # Handle file fields separately to allow partial updates
        if "logo" not in validated_data:
            validated_data["logo"] = instance.logo
        if "kyc_document" not in validated_data:
            validated_data["kyc_document"] = instance.kyc_document

        return super().update(instance, validated_data)
