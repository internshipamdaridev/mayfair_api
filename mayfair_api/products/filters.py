import django_filters
from django.db.models import Q
from .models import Product, Category, ProductAttributeValue


class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    description = django_filters.CharFilter(lookup_expr="icontains")
    sku = django_filters.CharFilter(lookup_expr="iexact")
    slug = django_filters.CharFilter(lookup_expr="iexact")

    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")

    min_discount_price = django_filters.NumberFilter(
        field_name="discount_price", lookup_expr="gte"
    )
    max_discount_price = django_filters.NumberFilter(
        field_name="discount_price", lookup_expr="lte"
    )

    in_stock = django_filters.BooleanFilter(method="filter_in_stock")
    is_active = django_filters.BooleanFilter()

    category = django_filters.CharFilter(method="filter_category")
    vendor = django_filters.CharFilter(field_name="vendor__id")

    attributes = django_filters.CharFilter(method="filter_attributes")

    search = django_filters.CharFilter(method="filter_search")

    ordering = django_filters.OrderingFilter(
        fields=(
            ("price", "price"),
            ("discount_price", "discount_price"),
            ("created_at", "created_at"),
            ("updated_at", "updated_at"),
            ("name", "name"),
        ),
        field_labels={
            "price": "Price",
            "discount_price": "Discount Price",
            "created_at": "Creation Date",
            "updated_at": "Last Updated",
            "name": "Product Name",
        },
    )

    class Meta:
        model = Product
        fields = {
            "name": ["exact", "icontains"],
            "price": ["exact", "gte", "lte"],
            "discount_price": ["exact", "gte", "lte"],
            "stock": ["exact", "gte", "lte"],
        }

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__gt=0)
        return queryset.filter(stock=0)

    def filter_category(self, queryset, name, value):
        try:
            # Try to get category by ID first
            return queryset.filter(category__id=value)
        except ValueError:
            # If not an ID, try by slug
            return queryset.filter(category__slug=value)

    def filter_attributes(self, queryset, name, value):
        # Expected format: "color:red,size:large"
        attributes = value.split(",")

        for attr in attributes:
            if ":" in attr:
                attr_name, attr_value = attr.split(":", 1)
                queryset = queryset.filter(
                    attribute_values__attribute__name__iexact=attr_name.strip(),
                    attribute_values__value__iexact=attr_value.strip(),
                )
        return queryset.distinct()

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value)
            | Q(description__icontains=value)
            | Q(sku__icontains=value)
            | Q(attribute_values__value__icontains=value)
        ).distinct()
