from django.contrib import admin

from mayfair_api.products import models

# Register your models here.

admin.site.register(models.Category)
admin.site.register(models.Product)
admin.site.register(models.ProductImage)
admin.site.register(models.ProductAttribute)
admin.site.register(models.ProductAttributeValue)
