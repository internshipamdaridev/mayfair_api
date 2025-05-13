import uuid
import random
import string

from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator

from mayfair_api.accounts.models import VendorProfile


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.FileField(upload_to="category_images/", blank=True, null=True)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Only generate slug if it doesn't exist
        if not self.slug and self.name:
            base_slug = slugify(self.name)
            self.slug = base_slug
        super().save(*args, **kwargs)


class Product(models.Model):
    vendor = models.ForeignKey(
        VendorProfile, on_delete=models.CASCADE, related_name="products"
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="products"
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    short_description = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    discount_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
    )
    stock = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Only generate slug if it doesn't exist
        if not self.slug and self.name:
            self.slug = self.generate_unique_slug()

        # Auto-generate SKU if empty
        if not self.sku:
            self.sku = f"PROD-{uuid.uuid4().hex[:6]}"

        super().save(*args, **kwargs)

    def generate_unique_slug(self):
        base_slug = slugify(self.name)
        new_slug = base_slug

        # Only add randomness if slug exists
        if Product.objects.filter(slug=new_slug).exists():
            random_suffix = "".join(
                random.choices(string.ascii_lowercase + string.digits, k=4)
            )
            new_slug = f"{base_slug}-{random_suffix}"

        return new_slug


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="product_images/")
    alt_text = models.CharField(max_length=255, blank=True)
    is_feature = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.name}"


class ProductAttribute(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class ProductAttributeValue(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="attribute_values"
    )
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"
