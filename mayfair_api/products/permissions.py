from rest_framework.permissions import BasePermission


class IsVendor(BasePermission):
    def has_permission(self, request, view):
        return request.user.user_type == "vendor"


class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return request.user.user_type == "customer"
