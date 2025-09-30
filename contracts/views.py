from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status, permissions, serializers
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import Contract, Milestone, AuditTrail
from .serializers import ContractSerializer, ContractCreateSerializer, MilestoneSerializer
from .permissions import IsClient, IsFreelancer, IsContractParty, IsClientOrFreelancer


class ContractViewSet(ModelViewSet):
    """
        ViewSet for managing contracts.
        - create: Client creates a new contract.
        - list/retrieve: List or get details of contracts.
        - update: Update contract details.
        """
    queryset = Contract.objects.all()
    permission_classes = [IsClientOrFreelancer]
    serializer_class = ContractSerializer



    def get_serializer_class(self):
        if self.action == 'create':
            return ContractCreateSerializer
        return ContractSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Contract.objects.all()
        return Contract.objects.filter(Q(client=user) | Q(freelancer=user))

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)

class ContractAcceptView(APIView):
    """
        Freelancer accepts a contract that is in 'pending_acceptance' state.
    """
    permission_classes = [IsFreelancer]

    def patch(self, request, pk):
        contract = get_object_or_404(Contract, pk=pk)
        if contract.status != 'pending_acceptance':
            return Response({"error": "Contract is not pending acceptance"}, status=status.HTTP_400_BAD_REQUEST)
        if contract.freelancer != request.user:
            return Response({"error": "Only the assigned freelancer can accept"}, status=status.HTTP_403_FORBIDDEN)
        contract.status = 'active'
        contract.expiry_date = None  # Clear expiry on acceptance
        contract.save()
        AuditTrail.objects.create(
            contract=contract,
            performed_by=request.user,
            action='contract_accepted',
            details={'status': contract.status}
        )
        return Response(ContractSerializer(contract).data)

class ContractRejectView(APIView):
    """
        Freelancer rejects a contract that is in 'pending_acceptance' state.
    """
    permission_classes = [IsFreelancer]

    def patch(self, request, pk):
        contract = get_object_or_404(Contract, pk=pk)
        if contract.status != 'pending_acceptance':
            return Response({"error": "Contract is not pending acceptance"}, status=status.HTTP_400_BAD_REQUEST)
        if contract.freelancer != request.user:
            return Response({"error": "Only the assigned freelancer can reject"}, status=status.HTTP_403_FORBIDDEN)
        contract.status = 'Rejected'
        contract.expiry_date = None
        contract.save()
        AuditTrail.objects.create(
            contract=contract,
            performed_by=request.user,
            action='contract_rejected',
            details={'status': contract.status}
        )
        return Response(ContractSerializer(contract).data)

"""class ContractCancelView(APIView):
    ""
        Client or freelancer cancels a contract that is in 'draft' or 'pending_acceptance'.
    ""
    permission_classes = [IsClientOrFreelancer]

    def patch(self, request, pk):
        contract = get_object_or_404(Contract, pk=pk)
        if contract.status not in ['draft', 'pending_acceptance']:
            return Response({"error": "Only draft or pending contracts can be cancelled"}, status=status.HTTP_400_BAD_REQUEST)
        if not (request.user == contract.client or request.user == contract.freelancer or request.user.is_staff):
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
        contract.status = 'cancelled'
        contract.expiry_date = None
        contract.save()
        AuditTrail.objects.create(
            contract=contract,
            performed_by=request.user,
            action='contract_cancelled',
            details={'status': contract.status}
        )
        return Response(ContractSerializer(contract).data)
"""

"""class ContractMarkCompleteView(APIView):
    ""
        Client marks a contract as completed (only when in 'in_review' state).
    ""
    permission_classes = [IsClient, IsContractParty]

    def patch(self, request, pk):
        contract = get_object_or_404(Contract, pk=pk)
        if contract.status != 'in_review':
            return Response({"error": "Contract must be in review to mark complete"}, status=status.HTTP_400_BAD_REQUEST)
        contract.status = 'completed'
        #contract.escrow_status = 'released'  # Release funds on completion
        contract.save()
        AuditTrail.objects.create(
            contract=contract,
            performed_by=request.user,
            action='contract_completed',
            details={'status': contract.status, 'escrow_status': contract.escrow_status}
        )
        return Response(ContractSerializer(contract).data)
"""


class ContractDisputeView(APIView):
    """
        Either client or freelancer can raise a dispute on an active or in-review contract.
    """
    permission_classes = [IsClientOrFreelancer]

    def patch(self, request, pk):
        contract = get_object_or_404(Contract, pk=pk)
        if contract.status not in ['active', 'in_review']:
            return Response({"error": "Contract must be active or in review to raise a dispute"}, status=status.HTTP_400_BAD_REQUEST)
        if not (request.user == contract.client or request.user == contract.freelancer):
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
        contract.status = 'disputed'
        contract.dispute_reason = request.data.get('dispute_reason', '')
        contract.dispute_status = 'open'
        contract.save()
        AuditTrail.objects.create(
            contract=contract,
            performed_by=request.user,
            action='dispute_raised',
            details={'dispute_reason': contract.dispute_reason}
        )
        return Response(ContractSerializer(contract).data)

class ContractSubmitWorkView(APIView):
    """
       Freelancer submits work for a contract (moves it from 'active' → 'in_review').
    """
    permission_classes = [IsFreelancer, IsContractParty]

    def patch(self, request, pk):
        contract = get_object_or_404(Contract, pk=pk)
        if contract.status != 'active':
            return Response({"error": "Contract must be active to submit work"}, status=status.HTTP_400_BAD_REQUEST)
        if contract.freelancer != request.user:
            return Response({"error": "Only the assigned freelancer can submit work"}, status=status.HTTP_403_FORBIDDEN)
        contract.status = 'in_review'
        contract.save()
        AuditTrail.objects.create(
            contract=contract,
            performed_by=request.user,
            action='work_submitted',
            details={'status': contract.status}
        )
        return Response(ContractSerializer(contract).data)

class UserContractsView(APIView):
    """
       List all contracts for a given user (client or freelancer).
       """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        if request.user.id != user_id and not request.user.is_staff:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
        contracts = Contract.objects.filter(Q(client_id=user_id) | Q(freelancer_id=user_id))
        serializer = ContractSerializer(contracts, many=True)
        return Response(serializer.data)

class MilestoneViewSet(ModelViewSet):
    """
       ViewSet for managing milestones within a contract.
       - create: Add a milestone to a contract (only if active).
       - list/retrieve: List or get details of milestones for a contract.
       - update/delete: Update or remove milestones.
    """
    serializer_class = MilestoneSerializer
    permission_classes = [IsClient]

    def get_queryset(self):
        contract_id = self.kwargs.get('contract_id')
        return Milestone.objects.filter(contract_id=contract_id)

    def perform_create(self, serializer):
        contract = get_object_or_404(Contract, pk=self.kwargs['contract_id'])
        if contract.status != 'active' and not self.request.user.is_staff:
            raise serializers.ValidationError("Cannot add milestones to non-active contract")
        serializer.save(contract=contract)

"""class ContractDocumentViewSet(ModelViewSet):
    serializer_class = ContractDocumentSerializer
    permission_classes = [IsContractParty]

    def get_queryset(self):
        contract_id = self.kwargs.get('contract_id')
        return ContractDocument.objects.filter(contract_id=contract_id)

    def perform_create(self, serializer):
        contract = get_object_or_404(Contract, pk=self.kwargs['contract_id'])
        serializer.save(contract=contract, uploaded_by=self.request.user)
"""