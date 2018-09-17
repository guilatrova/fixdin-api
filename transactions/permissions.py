from rest_framework import permissions

from transactions.models import Category


class IsNotSystemTransactionOrIsReadOnly(permissions.BasePermission):
    """
    Object-level permissions to only allow safe methods to system generated transactions
    """
    message = "You can't directly manage auto generated system transactions"

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.category.kind != Category.SYSTEM_KIND
