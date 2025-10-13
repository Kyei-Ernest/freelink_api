from rest_framework import permissions

class BothClientAndFreelancer(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.client or request.user == obj.freelancer or request.user.is_staff

class IsClient(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_client

class IsFreelancer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_freelancer

class IsContractParty(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.client or request.user == obj.freelancer or request.user.is_staff


class IsClientOrFreelancer(permissions.BasePermission):
    """
    Clients can create/update contracts.
    Freelancers can only view (read-only).
    Staff (admin) can do everything.
    """

    def has_permission(self, request, view):
        # Allow staff full access
        if request.user and request.user.is_staff:
            return True

        # Allow safe methods (GET, HEAD, OPTIONS) for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        # Only clients can create or modify contracts
        if getattr(view, "action", None) == "create":
            return hasattr(request.user, "is_client") and request.user.is_client

        return True

    def has_object_permission(self, request, view, obj):
        # Staff can access everything
        if request.user and request.user.is_staff:
            return True

        # Freelancers can only read if they are part of the contract
        if request.method in permissions.SAFE_METHODS:
            return obj.client == request.user or obj.freelancer == request.user

        # Clients can edit only their own contracts
        return obj.client == request.user
