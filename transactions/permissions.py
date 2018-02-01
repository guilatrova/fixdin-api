from rest_framework import permissions
from transactions.models import BoundReasons

class IsNotTransfer(permissions.BasePermission):
    """
    Object-level permissions to only allow safe methods to transfers kind transactions
    """
    message = "You can't manage transfers through transactions endpoint"

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.bound_reason != BoundReasons.TRANSFER_BETWEEN_ACCOUNTS