from django.db.models import Q
from rest_framework import generics, permissions, filters, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from django_filters import rest_framework as django_filters


from .models import Product, Category, ProductAttribute
from .serializers import (
    ProductSerializer,
    CategorySerializer,
    ProductAttributeSerializer,
    ProductSuggestionSerializer,
    ProductAttributeValueSerializer,
)
from .permissions import IsVendor, IsCustomer
from .filters import ProductFilter  # Import the filter class we created


class ProductListView(generics.ListCreateAPIView):
    parser_classes = [MultiPartParser, FormParser]
    queryset = (
        Product.objects.filter(is_active=True)
        .select_related("vendor", "category")
        .prefetch_related("images", "attribute_values", "attribute_values__attribute")
    )
    serializer_class = ProductSerializer
    filter_backends = [
        django_filters.DjangoFilterBackend,
        # django_filters.SearchFilter,
        # django_filters.OrderingFilter,
    ]
    filterset_class = ProductFilter
    search_fields = ["name", "description", "sku", "attribute_values__value"]
    ordering_fields = [
        "price",
        "discount_price",
        "created_at",
        "updated_at",
        "name",
        "stock",
    ]

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def create(self, request, *args, **kwargs):
        # Your existing create logic remains unchanged
        print("theuser", request.user)
        print("Request data:", request.data)
        print("Request files:", request.FILES)

        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer):
        serializer.save(vendor=self.request.user.vendor_profile)


# class ProductListView(generics.ListCreateAPIView):
#     parser_classes = [MultiPartParser, FormParser]  # Add this line
#     queryset = Product.objects.filter(is_active=True)
#     serializer_class = ProductSerializer
#     filter_backends = [
#         DjangoFilterBackend,
#         filters.SearchFilter,
#         filters.OrderingFilter,
#     ]
#     filterset_fields = ["category", "vendor"]
#     search_fields = ["name", "description"]
#     ordering_fields = ["price", "created_at", "updated_at"]

#     def get_permissions(self):
#         if self.request.method == "POST":
#             return [
#                 permissions.IsAuthenticated(),
#             ]
#         return [permissions.AllowAny()]

#     def create(self, request, *args, **kwargs):
#         print("theuser", request.user)
#         print("Request data:", request.data)
#         print("Request files:", request.FILES)

#         serializer = self.get_serializer(
#             data=request.data, context={"request": request}
#         )
#         serializer.is_valid(raise_exception=True)
#         self.perform_create(serializer)
#         headers = self.get_success_headers(serializer.data)
#         return Response(
#             serializer.data, status=status.HTTP_201_CREATED, headers=headers
#         )

#     def perform_create(self, serializer):
#         serializer.save(vendor=self.request.user.vendor_profile)


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = "slug"

    # def update(self, request, *args, **kwargs):
    #     print("Request edited data:", request.data)
    #     return Response()

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [permissions.IsAuthenticated(), IsVendor()]
        return [permissions.AllowAny()]


class CategoryListView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsVendor()]
        return [permissions.AllowAny()]


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [permissions.IsAuthenticated(), IsVendor()]
        return [permissions.AllowAny()]


class ProductAttributeListView(generics.ListCreateAPIView):
    queryset = ProductAttribute.objects.all()
    serializer_class = ProductAttributeSerializer
    # permission_classes = [permissions.IsAuthenticated, IsVendor]


class ProductAttributeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductAttribute.objects.all()
    serializer_class = ProductAttributeSerializer
    permission_classes = [permissions.IsAuthenticated(), IsVendor()]


class ProductSearchSuggestionsView(APIView):
    def get(self, request):
        query = request.GET.get("q", "")
        if not query or len(query) < 2:
            return Response([])

        products = (
            Product.objects.filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(category__name__icontains=query),
                is_active=True,
            )
            .select_related("category")
            .prefetch_related("images")[:10]
        )

        serializer = ProductSuggestionSerializer(products, many=True)
        return Response(serializer.data)
