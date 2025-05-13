from django.urls import path
from .views import (
    ProductListView,
    ProductDetailView,
    CategoryListView,
    CategoryDetailView,
    ProductAttributeListView,
    ProductAttributeDetailView,
    ProductSearchSuggestionsView,
)

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path(
        "categories/<slug:slug>/", CategoryDetailView.as_view(), name="category-detail"
    ),
    path("attributes/", ProductAttributeListView.as_view(), name="attribute-list"),
    path(
        "attributes/<int:pk>/",
        ProductAttributeDetailView.as_view(),
        name="attribute-detail",
    ),
    path(
        "search-suggestions/",
        ProductSearchSuggestionsView.as_view(),
        name="product-list",
    ),
    path("<slug:slug>/", ProductDetailView.as_view(), name="product-detail"),
    path("", ProductListView.as_view(), name="product-list"),
]
