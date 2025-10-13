from decimal import Decimal

from .models import Transaction, EscrowAccount, Wallet


def fund_escrow_from_wallet(client_wallet: Wallet, escrow: EscrowAccount, amount: Decimal, *, reference: str = None, metadata: dict = None):
    """Convenience service to place a hold on client wallet and credit an escrow account.

    Creates a single `escrow_hold` transaction record and executes the movements
    atomically using the TransactionManager.
    """
    metadata = metadata or {}
    metadata.update({"action": "fund_escrow"})
    return Transaction.objects.create_transaction(wallet=client_wallet, escrow=escrow, amount=amount, type="escrow_hold", metadata={"reference": reference, **(metadata or {})})


def release_escrow_to_wallet(escrow: EscrowAccount, recipient_wallet: Wallet, amount: Decimal, *, reference: str = None, metadata: dict = None):
    metadata = metadata or {}
    metadata.update({"action": "release_escrow"})
    return Transaction.objects.create_transaction(wallet=recipient_wallet, escrow=escrow, amount=amount, type="escrow_release", metadata={"reference": reference, **(metadata or {})})


def refund_escrow_to_client(escrow: EscrowAccount, client_wallet: Wallet, amount: Decimal, *, reference: str = None, metadata: dict = None):
    metadata = metadata or {}
    metadata.update({"action": "refund"})
    return Transaction.objects.create_transaction(wallet=client_wallet, escrow=escrow, amount=amount, type="refund", metadata={"reference": reference, **(metadata or {})})
