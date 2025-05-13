from rest_framework import serializers

from .models import (
    Category,
    Product,
    ProductImage,
    ProductAttribute,
    ProductAttributeValue,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "image", "description", "created_at"]
        read_only_fields = ["slug", "created_at"]


class ProductAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttribute
        fields = ["id", "name", "description"]
        read_only_fields = ["created_at"]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "alt_text", "is_feature"]


class ProductAttributeValueSerializer(serializers.ModelSerializer):
    attribute = serializers.StringRelatedField()

    class Meta:
        model = ProductAttributeValue
        fields = ["attribute", "value"]


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    attribute_values = ProductAttributeValueSerializer(many=True, read_only=True)
    vendor = serializers.StringRelatedField(read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())

    class Meta:
        model = Product
        fields = [
            "id",
            "vendor",
            "category",
            "name",
            "slug",
            "description",
            "short_description",
            "price",
            "discount_price",
            "stock",
            "sku",
            "is_active",
            "created_at",
            "updated_at",
            "images",
            "attribute_values",
        ]
        extra_kwargs = {
            "slug": {"required": False},
            "sku": {"required": False},
        }
        read_only_fields = ["vendor"]

    def create(self, validated_data):
        request = self.context.get("request")

        # Create the product first
        product = Product.objects.create(**validated_data)

        # Process images
        image_data = {}
        for key, value in request.data.items():
            if key.startswith("images"):
                # Extract the index and field name
                parts = key.replace("]", "").split("[")
                if len(parts) == 3:
                    index = parts[1]
                    field = parts[2]

                    if index not in image_data:
                        image_data[index] = {}

                    image_data[index][field] = value

        # Now create image objects
        for index, fields in image_data.items():
            # Get image file from request.FILES
            image_key = f"images[{index}][image]"
            if image_key in request.FILES:
                image_file = request.FILES[image_key]
                alt_text = fields.get("alt_text", "")
                is_feature = fields.get("is_feature", "false") == "true"

                ProductImage.objects.create(
                    product=product,
                    image=image_file,
                    alt_text=alt_text,
                    is_feature=is_feature,
                )

        # Process attribute values
        attr_value_data = {}
        for key, value in request.data.items():
            if key.startswith("attribute_values"):
                parts = key.replace("]", "").split("[")
                if len(parts) == 3:
                    index = parts[1]
                    field = parts[2]

                    if index not in attr_value_data:
                        attr_value_data[index] = {}

                    attr_value_data[index][field] = value

        # Create attribute value objects
        for index, fields in attr_value_data.items():
            attribute_id = fields.get("attribute")
            value = fields.get("value")

            if attribute_id and value:
                try:
                    attribute = ProductAttribute.objects.get(id=attribute_id)
                    ProductAttributeValue.objects.create(
                        product=product, attribute=attribute, value=value
                    )
                except ProductAttribute.DoesNotExist:
                    pass  # Handle error appropriately

        return product


class ProductSuggestionSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True)
    # category = serializers.CharField(source="category.name")
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())

    class Meta:
        model = Product
        fields = ["id", "name", "slug", "price", "category", "images"]


# class ProductSerializer(serializers.ModelSerializer):
#     images = ProductImageSerializer(many=True, read_only=True)
#     attribute_values = ProductAttributeValueSerializer(many=True, read_only=True)
#     vendor = serializers.StringRelatedField()
#     category = serializers.StringRelatedField()

#     class Meta:
#         model = Product
#         fields = [
#             "id",
#             "vendor",
#             "category",
#             "name",
#             "slug",
#             "description",
#             "price",
#             "discount_price",
#             "stock",
#             "sku",
#             "is_active",
#             "created_at",
#             "updated_at",
#             "images",
#             "attribute_values",
#         ]
#         extra_kwargs = {
#             "slug": {"required": False},
#             "sku": {"required": False},
#             # "vendor": {"required": False},
#         }
#         read_only_fields = ["vendor"]
