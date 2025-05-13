from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin  #
from django.utils import timezone
from django.core.validators import RegexValidator
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractBaseUser, PermissionsMixin):
    from .managers import UserManager

    USER_TYPE_CHOICES = (
        ("customer", "Customer"),
        ("vendor", "Vendor"),
    )

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    user_type = models.CharField(
        max_length=10, choices=USER_TYPE_CHOICES, default="customer"
    )
    email = models.EmailField(max_length=80, unique=True)
    phone_number = PhoneNumberField(unique=True)
    url = models.SlugField(max_length=100, unique=True)
    profile_picture = models.ImageField(
        upload_to="profile_pics/", blank=True, null=True
    )
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["phone_number", "first_name", "last_name"]

    objects = UserManager()

    def __str__(self):
        return self.email


class VendorProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="vendor_profile"
    )
    email = models.EmailField(max_length=80, unique=True)
    phone_number = PhoneNumberField(unique=True)
    business_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    line1 = models.TextField(blank=True, null=True)
    line2 = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    logo = models.ImageField(upload_to="vendor_logos/", blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True)
    kyc_verified = models.BooleanField(default=False)
    kyc_document = models.FileField(upload_to="kyc_documents/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.business_name


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="customer_profile"
    )
    shipping_address = models.TextField(blank=True)
    billing_address = models.TextField(blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email
