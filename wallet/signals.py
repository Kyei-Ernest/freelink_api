from django.contrib.auth import get_user_model
from django.db.models.signals import post_save,pre_save
from django.dispatch import receiver
from requests import request
from contracts.models import Contract
from .models import EscrowAccount, Transaction, TransactionManager, Wallet
from decimal import Decimal


from .models import Currency, Wallet


User = get_user_model()

@receiver(post_save, sender=User)
def create_user_wallet(sender, instance, created, **kwargs):

    """
    Automatically create a wallet  for each new user.
    Currency is determined by the user's country if possible.
    """

    COUNTRY_CURRENCY_MAP = {
        "GH": "GHS",
        "USA": "USD",
        "UK": "GBP",
        "NG": "NGN",
        # add more as needed
    }

    if created:
        # get currency code from user's country (fallback to USD)
        currency_code = COUNTRY_CURRENCY_MAP.get(instance.country, "USD")

        # fetch the Currency object
        default_currency = Currency.objects.filter(code=currency_code).first()

        # create wallet only if user doesn't already have one
        if not hasattr(instance, "wallet"):
            Wallet.objects.create(user=instance, currency=default_currency)
            
        
        if created and instance.is_client:
                EscrowAccount.objects.create(
                    user=instance,
                    reference=f"client-{instance.id}-escrow",
                    currency=Currency.objects.first(),
                    balance=Decimal("0.00"),
        )





@receiver(pre_save, sender=Contract)
def run_function_when_active(sender, instance, **kwargs):
    """
    Run this before saving a Contract.
    Only triggers when the status changes to 'active'.
    """
    if not instance.pk:
        # Skip new contracts (since they have no previous status)
        return

    # Get the existing version from the database
    try:
        old_instance = Contract.objects.get(pk=instance.pk)
    except Contract.DoesNotExist:
        return

    # Check if the status changed from something else to 'active'
    if old_instance.status != 'active' and instance.status == 'active':
        # The contract just became active
        # Call your custom function here

        print("THis is the instance : ",instance.escrow_status)

        wallet = Wallet.objects.get(user = instance.client.id)
        escrow_account = EscrowAccount.objects.get(user = instance.client.id)

        instance.escrow_status = "funded"

        Transaction.objects.create_transaction(
            wallet=wallet,
            escrow=escrow_account,
            amount=Decimal(instance.agreed_bid),
            type='escrow_hold',
            status='pending',
            metadata={'contract_id': str(Contract.id)},
            related_object=Contract
        )

        





