from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from .models import Wallet, Currency


class WalletSerializer(ModelSerializer):
    currency = serializers.SlugRelatedField(
        slug_field="code", read_only=True
    )

    class Meta:
        model = Wallet
        fields = [
            "id",
            "user",
            "currency",
            "balance",
            "available_balance",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "balance",
            "currency",
            "available_balance",
            "created_at",
            "updated_at",
            "user",
        ]


class CurrencySerializer(ModelSerializer):
    class Meta:
        model = Currency
        fields = "__all__"
