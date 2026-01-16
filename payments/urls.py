from django.urls import path
from .views import (
    InitPaymentView,
    VerifyPaymentView,
    CreateBankRecipientView,
    CreateMobileMoneyRecipientView,
    GetBanksView,
    InitiateTransferView,
    # VerifyTransferView,
)

urlpatterns = [
    # 🔹 Payments
    path("init/", InitPaymentView.as_view(), name="init-payment"),
    path("verify/", VerifyPaymentView.as_view(), name="verify-payment"),

    # 🔹 Recipients
    path("create-bank-recipient/", CreateBankRecipientView.as_view(), name="create-bank-recipient"),
    path("create-momo-recipient/", CreateMobileMoneyRecipientView.as_view(), name="create-momo-recipient"),

    # 🔹 Banks
    path("get-banks/", GetBanksView.as_view(), name="get-banks"),

    # 🔹 Transfers
    path("initiate-transfer/", InitiateTransferView.as_view(), name="init-transfer"),
    # path("verify-transfer/<str:transfer_code>/", VerifyTransferView.as_view(), name="verify-transfer"),
]
