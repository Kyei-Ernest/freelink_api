from rest_framework.permissions import BasePermission

class IsSenderOrRecipient(BasePermission):
    """
    Custom permission: Only sender or recipient can access the message.
    """
    def has_object_permission(self, request, view, obj):
        return obj.sender == request.user or obj.recipient == request.user
