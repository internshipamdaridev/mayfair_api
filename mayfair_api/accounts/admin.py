from django.contrib import admin
from mayfair_api.accounts import models

# Register your models here.
admin.site.register(models.User)
admin.site.register(models.CustomerProfile)
admin.site.register(models.VendorProfile)
