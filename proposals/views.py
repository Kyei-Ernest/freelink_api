from rest_framework import generics, permissions, serializers
from django.shortcuts import get_object_or_404
from .models import Proposal
from .permissions import IsFreelancerUser, IsProposalOwner, IsJobOwnerForStatus
from .serializers import ProposalSerializer, ProposalStatusSerializer
from jobs.models import Job
from contracts.models import Contract



class ProposalListCreateView(generics.ListCreateAPIView):
    """
    - GET:
        * Freelancers → List their own proposals.
        * Clients → List proposals received for their jobs.
    - POST:
        * Freelancers submit a new proposal for a job.
    """
    serializer_class = ProposalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_freelancer:
            return Proposal.objects.filter(freelancer=user)
        elif user.is_client:
            return Proposal.objects.filter(job__client=user)
        return Proposal.objects.none()

    def get_permissions(self):
        if self.request.method == 'POST':
            self.permission_classes = [permissions.IsAuthenticated, IsFreelancerUser]
        return super().get_permissions()

    def perform_create(self, serializer):
        job_id = self.request.data.get('job')
        job = get_object_or_404(Job, pk=job_id)

        # Optional check: ensure job is still available
        if job.status != 'available':
            raise serializers.ValidationError("Proposals can only be submitted to available jobs.")

        serializer.save(freelancer=self.request.user, job=job)


class ProposalRetrieveView(generics.RetrieveAPIView):
    """
    Retrieve a single proposal.
    Accessible by:
      - Freelancer who submitted it
      - Client who owns the job
    """
    queryset = Proposal.objects.all()
    serializer_class = ProposalSerializer
    permission_classes = [permissions.IsAuthenticated, IsProposalOwner]


class ProposalUpdateStatusView(generics.UpdateAPIView):
    """
    Endpoint for clients to update a proposal's status.
    - Accept: Creates a Contract, marks job 'in_progress', declines others.
    - Decline: Simply marks proposal as declined.
    """
    queryset = Proposal.objects.all()
    serializer_class = ProposalStatusSerializer
    permission_classes = [permissions.IsAuthenticated, IsJobOwnerForStatus]

    def perform_update(self, serializer):
        proposal = self.get_object()
        new_status = serializer.validated_data['status']

        if new_status == 'accepted' and proposal.status != 'accepted':
            # 1. Create a Contract
            Contract.objects.create(
                job=proposal.job,
                freelancer=proposal.freelancer,
                client=proposal.job.client,
                agreed_bid=proposal.bid
            )
            # 2. Update the Job status
            proposal.job.status = 'in_progress'
            proposal.job.freelancer = proposal.freelancer
            proposal.job.save()
            # 3. Decline all other proposals for this job
            Proposal.objects.filter(job=proposal.job).exclude(id=proposal.id).update(status='declined')

        serializer.save()
