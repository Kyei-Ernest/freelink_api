from django.utils import timezone
from rest_framework import serializers
from .models import Contract, Milestone, AuditTrail, ContractDocument
from jobs.models import Job
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email']

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'title', 'description', 'budget', 'duration', 'deadline', 'status']

class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = ['id', 'description', 'due_date', 'amount', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class ContractSerializer(serializers.ModelSerializer):
    client = UserSerializer(read_only=True)
    freelancer = UserSerializer(read_only=True)
    job = JobSerializer(read_only=True)
    milestones = MilestoneSerializer(many=True, read_only=True)
    audit_trails = serializers.SerializerMethodField()

    


    class Meta:
        model = Contract
        fields = [
            'id', 'job', 'client', 'freelancer',
            'contract_text', 'terms',
            'agreed_bid', 'currency',
            'status', 'escrow_status', 'escrow_amount',
            'start_date', 'expiry_date',
            'created_at', 'updated_at', 'milestones', 'audit_trails'
        ]
        read_only_fields = [
            'id', 'agreed_bid', 'created_at', 'updated_at',
            'client', 'freelancer'
        ]

    def get_audit_trails(self, obj):
        # Include recent audit trails for in-app visibility
        audit_trails = obj.audit_trails.order_by('-timestamp')[:10]
        return AuditTrailSerializer(audit_trails, many=True).data

    """def get_documents(self, obj):
        # Include documents for in-app access
        documents = obj.documents.all()
        return ContractDocumentSerializer(documents, many=True).data"""

class ContractCreateSerializer(serializers.ModelSerializer):
    job_id = serializers.PrimaryKeyRelatedField(queryset=Job.objects.all(), source='job')
    freelancer_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(is_freelancer=True), source='freelancer')
    milestones = MilestoneSerializer(many=True, required=False)

    class Meta:
        model = Contract
        fields = ['id', 'job_id', 'freelancer_id', 'terms', 'agreed_bid', 'currency', 'milestones']

    def validate(self, data):
        if data['job'].client != self.context['request'].user:
            raise serializers.ValidationError("You can only create contracts for your own jobs.")
        if data['job'].status != 'in_progress':
            raise serializers.ValidationError("Job must be in progress to create a contract.")
        if Contract.objects.filter(job=data['job']).exists():
            raise serializers.ValidationError("A contract already exists for this job.")
        if data['agreed_bid'] > data['job'].budget:
            raise serializers.ValidationError("Agreed bid cannot exceed job budget.")
        if data['freelancer'] != data['job'].freelancer:
            raise serializers.ValidationError("Freelancer must match job's assigned freelancer.")
        return data

    def create(self, validated_data):
        milestones_data = validated_data.pop('milestones', [])
        contract = Contract.objects.create(
            client=self.context['request'].user,
            escrow_amount=validated_data['agreed_bid'],
            status='pending_acceptance',  # Directly to pending_acceptance for in-app flow
            expiry_date=timezone.now() + timezone.timedelta(days=7),
            **validated_data
        )
        for milestone_data in milestones_data:
            Milestone.objects.create(contract=contract, **milestone_data)
        AuditTrail.objects.create(
            contract=contract,
            user=self.context['request'].user,
            action='contract_created',
            details={'status': contract.status, 'agreed_bid': str(contract.agreed_bid)}
        )
        return contract

class AuditTrailSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = AuditTrail
        fields = ['id', 'contract', 'user', 'action', 'details', 'timestamp']
        read_only_fields = ['id', 'timestamp']

"""class ContractDocumentSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)

    class Meta:
        model = ContractDocument
        fields = ['id', 'contract', 'file', 'description', 'uploaded_by', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_by', 'uploaded_at']"""
