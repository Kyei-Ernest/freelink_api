from rest_framework import generics, permissions, serializers
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample, OpenApiResponse
from .models import Proposal
from .permissions import IsFreelancerUser, IsProposalOwner, IsJobOwnerForStatus
from .serializers import ProposalSerializer, ProposalStatusSerializer
from jobs.models import Job
from contracts.models import Contract


@extend_schema_view(
    get=extend_schema(
        tags=['Proposals'],
        summary='List proposals',
        description='''
        Get a list of proposals.
        
        **For Freelancers:** Returns all proposals you have submitted.
        
        **For Clients:** Returns all proposals received for your jobs.
        
        **Proposal Statuses:**
        - `submitted`: Awaiting client review
        - `accepted`: Proposal accepted, contract created
        - `declined`: Proposal rejected by client
        - `withdrawn`: Withdrawn by freelancer
        '''
    ),
    post=extend_schema(
        tags=['Proposals'],
        summary='Submit a proposal',
        description='''
        Submit a new proposal for a job. **Only freelancers can submit proposals.**
        
        **Requirements:**
        - Job must be in `available` status
        - You cannot submit multiple proposals to the same job
        
        **Fields:**
        - `job`: Job ID to apply for
        - `cover_letter`: Your pitch for the job
        - `bid`: Your proposed price
        - `estimated_duration`: How long you expect to take (days)
        ''',
        examples=[
            OpenApiExample(
                'Submit Proposal',
                value={
                    "job": 1,
                    "cover_letter": "I am excited about this project! With 5 years of Django experience and 20+ e-commerce projects, I can deliver a high-quality solution.",
                    "bid": "2000.00",
                    "estimated_duration": 25
                },
                request_only=True
            )
        ],
        responses={
            201: OpenApiResponse(description='Proposal submitted successfully'),
            400: OpenApiResponse(description='Validation error or job not available'),
            403: OpenApiResponse(description='Only freelancers can submit proposals')
        }
    )
)
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


@extend_schema(
    tags=['Proposals'],
    summary='Get proposal details',
    description='''
    Retrieve details of a specific proposal.
    
    **Accessible by:**
    - The freelancer who submitted it
    - The client who owns the job
    '''
)
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


@extend_schema(
    tags=['Proposals'],
    summary='Accept or decline a proposal',
    description='''
    Update the status of a proposal. **Only the job owner (client) can do this.**
    
    **Actions:**
    - `accepted`: Creates a contract, assigns freelancer, declines other proposals
    - `declined`: Rejects this proposal
    
    **What happens when accepted:**
    1. A new Contract is created between client and freelancer
    2. The job status changes to `in_progress`
    3. The freelancer is assigned to the job
    4. All other proposals for this job are automatically declined
    ''',
    examples=[
        OpenApiExample(
            'Accept Proposal',
            value={"status": "accepted"},
            request_only=True
        ),
        OpenApiExample(
            'Decline Proposal',
            value={"status": "declined"},
            request_only=True
        )
    ],
    responses={
        200: OpenApiResponse(description='Status updated successfully'),
        403: OpenApiResponse(description='Only the job owner can update proposal status')
    }
)
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

