from decimal import Decimal
from uuid import uuid4

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import F
from django.utils import timezone

User = settings.AUTH_USER_MODEL


# Constants / Choices
TRANSACTION_TYPE_CHOICES = [
    ("deposit", "Deposit"),
    ("escrow_hold", "Escrow Hold"),
    ("escrow_release", "Escrow Release"),
    ("payout", "Payout"),
    ("withdrawal", "Withdrawal"),
    ("refund", "Refund"),
    ("fee", "Fee"),
    ("adjustment", "Adjustment"),
    ("transfer", "Internal Transfer"),
]

TRANSACTION_STATUS_CHOICES = [
    ("pending", "Pending"),
    ("completed", "Completed"),
    ("failed", "Failed"),
    ("cancelled", "Cancelled"),
]


class Currency(models.Model):
    """Optional currency table if you plan to support multiple currencies.

    You can pre-populate common currencies (USD, EUR, GHS) and reference them
    from wallets and transactions. If you prefer a lighter weight approach you
    can replace this with a CharField on Wallet and Transaction.
    """

    code = models.CharField(max_length=8, unique=True)  # e.g. "USD"
    name = models.CharField(max_length=64)
    symbol = models.CharField(max_length=8, blank=True, null=True)
    decimals = models.PositiveSmallIntegerField(default=2)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.code


class Wallet(models.Model):
    """User-facing wallet.

    - One-to-one with a user (typical), but you could also make multiple wallets
      per user (e.g. per currency, per product).
    - Balance is stored as Decimal for accuracy. All balance changes MUST go
      through `Wallet.adjust_balance` or `Transaction` creation routines.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet")
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, null=True, blank=True)
    balance = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal("0.0"))
    available_balance = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal("0.0"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["user"])]

    def __str__(self):
        return f"Wallet({self.user}, {self.balance})"

    def refresh_from_db_balances(self):
        """Reload balances from DB. Useful inside transactions."""
        self.refresh_from_db(fields=["balance", "available_balance"])

    def can_debit(self, amount: Decimal, require_available: bool = True) -> bool:
        """Check whether wallet has enough funds.

        If `require_available` is True then checks against `available_balance`
        (i.e., funds not on hold/escrow). If False, checks the raw balance.
        """
        if require_available:
            return self.available_balance >= Decimal(amount)
        return self.balance >= Decimal(amount)

    def adjust_balance(self, amount: Decimal, *, allow_negative: bool = False) -> None:
        """Atomically adjust the wallet balance and updated_at.

        Positive `amount` increments balance; negative decrements. This method
        only updates the `balance` field — callers should also change
        `available_balance` when placing/removing holds.
        """
        if not allow_negative and Decimal(amount) < 0:
            # ensure we have enough funds
            if self.balance + Decimal(amount) < Decimal("0.0"):
                raise ValueError("Insufficient funds")

        # Use F expressions to avoid race conditions
        Wallet.objects.filter(pk=self.pk).update(balance=F("balance") + Decimal(amount), updated_at=timezone.now())
        # refresh local instance
        self.refresh_from_db_balances()

    def place_hold(self, amount: Decimal):
        """Move funds from available_balance into hold (reduce available).

        This doesn't change `balance`, but prevents available funds from being
        spent. Typical for escrow_hold.
        """
        if self.available_balance < Decimal(amount):
            raise ValueError("Insufficient available funds to place hold")
        Wallet.objects.filter(pk=self.pk).update(available_balance=F("available_balance") - Decimal(amount), updated_at=timezone.now())
        self.refresh_from_db_balances()

    def release_hold(self, amount: Decimal):
        """Release a previously placed hold back to available_balance."""
        Wallet.objects.filter(pk=self.pk).update(available_balance=F("available_balance") + Decimal(amount), updated_at=timezone.now())
        self.refresh_from_db_balances()


class EscrowAccount(models.Model):
    """Represent an escrow pool tied to a contract or milestone.

    You might have many escrow accounts (one per milestone) or a single escrow
    account per contract. The EscrowAccount holds funds until release/refund.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='escrow_account')
    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
    reference = models.CharField(max_length=128, blank=True, null=True)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, null=True, blank=True)
    balance = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal("0.0"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["reference"])]

    def __str__(self):
        return f"EscrowAccount({self.reference}, {self.balance})"

    def credit(self, amount: Decimal):
        with transaction.atomic():
            EscrowAccount.objects.filter(pk=self.pk).update(balance=F("balance") + Decimal(amount), updated_at=timezone.now())
            self.refresh_from_db(fields=["balance"])  # refresh the instance

    def debit(self, amount: Decimal):
        with transaction.atomic():
            self.refresh_from_db(fields=["balance"])
            if self.balance < Decimal(amount):
                raise ValueError("Insufficient escrow balance")
            EscrowAccount.objects.filter(pk=self.pk).update(balance=F("balance") - Decimal(amount), updated_at=timezone.now())
            self.refresh_from_db(fields=["balance"])  # refresh


class TransactionManager(models.Manager):
    def create_transaction(self, *, wallet: Wallet = None, escrow: EscrowAccount = None, amount: Decimal, type: str, status: str = "pending", metadata: dict = None, related_object=None):
        """Creates a transaction record and performs bookkeeping.

        - For deposits: increase wallet.balance and available_balance
        - For escrow_hold: move available_balance -> escrow (via wallet.place_hold and escrow.credit)
        - For escrow_release: move escrow -> wallet (escrow.debit then wallet.adjust)

        The `related_object` field is generic contextual reference (e.g. Contract, Milestone id)
        """
        if amount == 0:
            raise ValueError("Transaction amount cannot be zero")

        metadata = metadata or {}

        # Ensure either wallet or escrow is provided, depending on type
        tx = self.model(
            uuid=uuid4(),
            wallet=wallet,
            escrow=escrow,
            amount=Decimal(amount),
            type=type,
            status=status,
            metadata=metadata,
            created_at=timezone.now(),
            related_object_type=metadata.get("related_type"),
            related_object_id=metadata.get("related_id"),
            reference=metadata.get("reference") or str(uuid4())[:32],
        )

        # Business logic: perform balance moves inside atomic block
        with transaction.atomic():
            tx.save()

            # handle common types
            if type == "deposit":
                if not wallet:
                    raise ValueError("Deposit requires a wallet")
                # increment both balance and available balance
                Wallet.objects.filter(pk=wallet.pk).update(balance=F("balance") + Decimal(amount), available_balance=F("available_balance") + Decimal(amount), updated_at=timezone.now())
                wallet.refresh_from_db_balances()
                tx.status = "completed"
                tx.save(update_fields=["status"])

            elif type == "escrow_hold":
                if not wallet or not escrow:
                    raise ValueError("Escrow hold requires wallet and escrow")
                # place hold and move funds to escrow balance
                wallet.place_hold(amount)
                escrow.credit(amount)
                tx.status = "completed"
                tx.save(update_fields=["status"])

            elif type == "escrow_release":
                if not wallet or not escrow:
                    raise ValueError("Escrow release requires wallet and escrow")
                # move from escrow to wallet
                escrow.debit(amount)
                Wallet.objects.filter(pk=wallet.pk).update(balance=F("balance") + Decimal(amount), updated_at=timezone.now())
                wallet.refresh_from_db_balances()
                tx.status = "completed"
                tx.save(update_fields=["status"])

            elif type == "payout" or type == "withdrawal":
                if not wallet:
                    raise ValueError("Payout/withdrawal requires wallet")
                # debit wallet.balance (payouts reduce balance and available)
                wallet.refresh_from_db_balances()
                if wallet.available_balance < Decimal(amount):
                    raise ValueError("Insufficient available balance for payout")
                Wallet.objects.filter(pk=wallet.pk).update(balance=F("balance") - Decimal(amount), available_balance=F("available_balance") - Decimal(amount), updated_at=timezone.now())
                wallet.refresh_from_db_balances()
                tx.status = "completed"
                tx.save(update_fields=["status"])

            elif type == "refund":
                # refunds typically debit escrow and credit client wallet
                if not wallet or not escrow:
                    raise ValueError("Refund requires wallet and escrow")
                escrow.debit(amount)
                Wallet.objects.filter(pk=wallet.pk).update(balance=F("balance") + Decimal(amount), available_balance=F("available_balance") + Decimal(amount), updated_at=timezone.now())
                wallet.refresh_from_db_balances()
                tx.status = "completed"
                tx.save(update_fields=["status"])

            elif type == "fee":
                # fees reduce a wallet and are held by platform; platform accounting handled externally
                if not wallet:
                    raise ValueError("Fee requires wallet")
                wallet.refresh_from_db_balances()
                if wallet.available_balance < Decimal(amount):
                    raise ValueError("Insufficient available balance for fee")
                Wallet.objects.filter(pk=wallet.pk).update(balance=F("balance") - Decimal(amount), available_balance=F("available_balance") - Decimal(amount), updated_at=timezone.now())
                wallet.refresh_from_db_balances()
                tx.status = "completed"
                tx.save(update_fields=["status"])

            else:
                # generic transfer/adjustment
                tx.status = "completed"
                tx.save(update_fields=["status"])

        return tx


class Transaction(models.Model):
    """Record of every monetary event affecting wallets and escrows.

    - `wallet` is the wallet affected by the transaction (nullable for escrow-only)
    - `escrow` is used for escrow movements
    - `related_object_type`/`related_object_id` form a very small generic relation pattern
    """

    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
    reference = models.CharField(max_length=128, unique=True)

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, null=True, blank=True, related_name="transactions")
    escrow = models.ForeignKey(EscrowAccount, on_delete=models.CASCADE, null=True, blank=True, related_name="transactions")

    amount = models.DecimalField(max_digits=18, decimal_places=6, validators=[MinValueValidator(Decimal("0.000001"))])
    type = models.CharField(max_length=32, choices=TRANSACTION_TYPE_CHOICES)
    status = models.CharField(max_length=16, choices=TRANSACTION_STATUS_CHOICES, default="pending")

    # very small generic relation for context (e.g. contract id, milestone id)
    related_object_type = models.CharField(max_length=128, null=True, blank=True)
    related_object_id = models.CharField(max_length=128, null=True, blank=True)

    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TransactionManager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["reference"]), models.Index(fields=["wallet"]), models.Index(fields=["escrow"])]

    def __str__(self):
        return f"Tx({self.reference}, {self.type}, {self.amount}, {self.status})"


class Withdrawal(models.Model):
    """Track external withdrawals (to bank, mobile money, paypal, etc.)

    Payment provider integration details (status, provider_reference) are
    intentionally included so you can reconcile with external systems.
    """

    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="withdrawals")
    amount = models.DecimalField(max_digits=18, decimal_places=6)
    provider = models.CharField(max_length=64, blank=True, null=True)
    provider_reference = models.CharField(max_length=128, blank=True, null=True)

    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS_CHOICES, default="pending")
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-requested_at"]

    def __str__(self):
        return f"Withdrawal({self.wallet.user}, {self.amount}, {self.status})"


