from rest_framework import serializers


class DepositSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Deposit amount must be greater than zero.")
        return value






class MobileMoneyRecipientSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    account_number = serializers.CharField(max_length=20)
    service_provider = serializers.ChoiceField(choices=[('mtn', 'MTN'), ('vodafone', 'Vodafone'), ('tigo', 'AirtelTigo')])


class TransferSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    recipient_code = serializers.CharField(max_length=100)

class BankTransferRecipientSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    account_number = serializers.CharField(max_length=20)
    bank_code = serializers.CharField(max_length=50)