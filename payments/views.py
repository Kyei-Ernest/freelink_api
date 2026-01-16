import uuid
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from .serializers import DepositSerializer, TransferSerializer
from .serializers import BankTransferRecipientSerializer, MobileMoneyRecipientSerializer
from .services.paystack import (
    initialize_payment,
    verify_payment,
    Paystack,
    initiate_transfer,
    create_transfer_recipient
)


class InitPaymentView(APIView):
    """
    Initialize a Paystack payment for a user.

    POST:
    - Body: { "amount": <amount> }
    - Uses logged-in user's email for Paystack.
    - Creates a Payment record and returns the Paystack payment link.
    """
    serializer_class = DepositSerializer

    def post(self, request):
        user = request.user
        amount = request.data.get("amount")
        res = initialize_payment(user, amount)

        return Response(res, status=status.HTTP_200_OK if res.get("status") else status.HTTP_400_BAD_REQUEST)


class VerifyPaymentView(APIView):
    """
    Verify a Paystack payment transaction.

    GET:
    - Query: ?reference=<transaction_reference>
    - Confirms transaction status and updates user's wallet balance if successful.
    """
    def get(self, request):
        reference = request.query_params.get("reference")
        result = verify_payment(reference)

        if "error" in result:
            return Response({"error": result["error"]}, status=result["status_code"])
        return Response(result["response"], status=result["status_code"])


class CreateBankRecipientView(APIView):
    """
    Create a new bank transfer recipient on Paystack.

    POST:
    - Body: { "name": <account_name>, "account_number": <account_no>, "bank_code": <bank_code> }
    - Returns a `recipient_code` used for initiating transfers.
    """
    serializer_class = BankTransferRecipientSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                recipient_code = create_transfer_recipient(
                    'nuban',
                    serializer.validated_data["name"],
                    serializer.validated_data["account_number"],
                    str(serializer.validated_data["bank_code"]),
                )
                return Response(
                    {"status": "success", "recipient_code": recipient_code},
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                return Response({"status": "error", "details": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class CreateMobileMoneyRecipientView(APIView):
    """
    Create a new mobile money payout recipient on Paystack.

    POST:
    - Body: { "name": <account_name>, "account_number": <wallet_number>, "service_provider": <momo_provider_code> }
    - Returns a `recipient_code` used for initiating transfers.
    """
    serializer_class = MobileMoneyRecipientSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                recipient_code = create_transfer_recipient(
                    'mobile_money',
                    serializer.validated_data["name"],
                    serializer.validated_data["account_number"],
                    serializer.validated_data["service_provider"],
                )
                return Response(
                    {"status": "success", "recipient_code": recipient_code},
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                return Response({"status": "error", "details": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class InitiateTransferView(APIView):
    """
    Initiate a transfer (withdrawal) to a Paystack recipient.

    POST:
    - Body: { "amount": <amount>, "recipient_code": <recipient_code> }
    - Generates a unique transaction reference.
    - Returns Paystack transfer response data.
    """
    serializer_class = TransferSerializer

    def post(self, request):
        amount = request.data.get("amount")
        recipient_code = request.data.get("recipient_code")

        if not amount or not recipient_code:
            return Response({"error": "Amount and recipient_code are required"}, status=status.HTTP_400_BAD_REQUEST)

        reference = str(uuid.uuid4()).replace("-", "")[:12]

        try:
            transfer_data = initiate_transfer(float(amount), recipient_code, reference)
            return Response(
                {"message": "Transfer initiated", "reference": reference, "data": transfer_data},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GetBanksView(APIView):
    """
    Fetch the list of available banks for Ghana from Paystack.

    GET:
    - Returns list of banks and their codes (used when creating bank recipients).
    """
    def get(self, request):
        paystack = Paystack()
        response = paystack.get_banks(country='ghana')

        if response['status']:
            return Response({
                'status': True,
                'data': response['data']
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': False,
                'message': response.get('message', 'Failed to fetch banks')
            }, status=status.HTTP_400_BAD_REQUEST)
