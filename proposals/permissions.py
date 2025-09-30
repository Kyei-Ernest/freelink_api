from rest_framework import permissions


class IsFreelancerUser(permissions.BasePermission):
    """
    Allow access only to authenticated users with is_freelancer = True.
    Used for submitting proposals.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_freelancer == True


class IsProposalOwner(permissions.BasePermission):
    """
    Freelancers can view their own proposals.
    Clients can view proposals submitted to their jobs.
    """
    def has_object_permission(self, request, view, obj):
        return obj.freelancer == request.user or obj.job.client == request.user


class IsJobOwnerForStatus(permissions.BasePermission):
    """
    Only the job owner (client) can update the status of a proposal.
    """
    def has_object_permission(self, request, view, obj):
        return obj.job.client == request.user

