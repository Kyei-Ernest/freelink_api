import uuid
from decimal import Decimal
import requests
from django.conf import settings
from payments.models import Payment
from wallet.models import Wallet


BASE_URL = "https://api.paystack.co"


def initialize_payment(user, amount):
    """
    Initialize a payment with Paystack.

    This creates a transaction on Paystack and generates a reference code
    to track the payment. It also stores a pending Payment record in the DB.

    Args:
        user (User): The authenticated user making the payment.
        amount (Decimal | int | float): The amount in GHS to be charged.

    Returns:
        dict: Paystack API response as JSON.
    """
    amount_in_pesewas = int(amount) * 100  # convert GHS → pesewas
    reference = str(uuid.uuid4()).replace("-", "")[:12]

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "email": user.email,
        "amount": amount_in_pesewas,
        "currency": "GHS",
        "reference": reference,
        "callback_url": "http://127.0.0.1:8000/api/payments/verify/",
    }

    r = requests.post(f"{BASE_URL}/transaction/initialize", json=data, headers=headers)
    res = r.json()

    if res.get("status"):
        # Save pending payment record in DB
        Payment.objects.create(user=user, amount=Decimal(amount), reference=reference)

    return res


def verify_payment(reference):
    """
    Verify the status of a Paystack payment.

    Fetches the payment status from Paystack using the reference, and updates:
    - Payment model (success/failed)
    - User's Wallet balance (if success)

    Args:
        reference (str): Unique transaction reference generated at initialization.

    Returns:
        dict: Contains Paystack response and local status code (200 or 404).
    """
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    r = requests.get(f"{BASE_URL}/transaction/verify/{reference}", headers=headers)
    res = r.json()

    try:
        payment = Payment.objects.get(reference=reference)
    except Payment.DoesNotExist:
        return {"error": "Payment not found", "status_code": 404}

    if res["data"]["status"] == "success":
        payment.status = "success"
        payment.save()

        wallet, _ = Wallet.objects.get_or_create(user=payment.user)
        wallet.balance += Decimal(res["data"]["amount"]) / Decimal(100)  # convert pesewas → GHS
        wallet.save()
    else:
        payment.status = "failed"
        payment.save()

    return {"response": res, "status_code": 200}


def create_transfer_recipient(account_type, name, account_number, service_provider):
    """Create a transfer recipient"""
    url = f"{BASE_URL}/transferrecipient"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "type": account_type,
        "name": name,
        "account_number": account_number,
        "bank_code": service_provider,
        "currency": "GHS",
    }


    res = requests.post(url, headers=headers, json=payload)

    try:
        res.raise_for_status()
    except Exception:
        print("Paystack Recipient Error:", res.json())
        raise

    return res.json()["data"]["recipient_code"]


def initiate_transfer(amount, recipient_code, reference):
    url = f"{BASE_URL}/transfer"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "source": "balance",
        "amount": int(float(amount) * 100),  # GHS → pesewas
        "recipient": recipient_code,
        "reference": reference,
        "reason": "User Withdrawal",
        "currency": "GHS"
    }

    res = requests.post(url, json=data, headers=headers)

    try:
        res.raise_for_status()
    except Exception:
        print("Paystack Transfer Error:", res.json())
        raise

    return res.json()


"""def verify_transfer(ref, *args, **kwargs):
    url = f"{BASE_URL}/transfer"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        response_data = response.json()
        return response_data['status'], response_data['data']
    response_data = response.json()
    return response_data['status'], response_data['message']
"""
class Paystack:
    PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY
    base_url = "https://api.paystack.co"

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {self.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

    # Existing payment verification method

    def get_banks(self, country='ghana'):
        """Get list of supported banks in Ghana"""
        path = f'/bank?country={country}'
        url = self.base_url + path
        response = requests.get(url, headers=self.headers)
        return response.json()

    def verify_transfer(self, transfer_code):
        """Verify transfer status"""
        path = f'/transfer/{transfer_code}'
        url = self.base_url + path
        response = requests.get(url, headers=self.headers)
        return response.json()

    def list_transfers(self, per_page=50, page=1):
        """List all transfers"""
        path = f'/transfer?perPage={per_page}&page={page}'
        url = self.base_url + path
        response = requests.get(url, headers=self.headers)
        return response.json()


# Future extensions (uncomment if needed):
"""
def verify_transfer(transfer_code):
    '''
    Verify transfer status by transfer code.

    Args:
        transfer_code (str): Paystack transfer code.

    Returns:
        dict: Paystack API response as JSON.
    '''
    url = f"{BASE_URL}/transfer/{transfer_code}"
    response = requests.get(url, headers=self.headers)
    return response.json()


def list_transfers(per_page=50, page=1):
    '''
    List all transfers (paginated).

    Args:
        per_page (int): Number of results per page.
        page (int): Page number.

    Returns:
        dict: Paginated list of transfers from Paystack.
    '''
    url = f"{BASE_URL}/transfer?perPage={per_page}&page={page}"
    response = requests.get(url, headers=self.headers)
    return response.json()
"""
