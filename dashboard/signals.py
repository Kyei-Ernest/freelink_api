from django.db.models.signals import post_save
from django.dispatch import receiver
#from transactions.models import Transaction
#from escrow.models import Escrow, EscrowDispute
from chat.models import Message

#@receiver(post_save, sender=Transaction)
#@receiver(post_save, sender=Escrow)
#@receiver(post_save, sender=EscrowDispute)
@receiver(post_save, sender=Message)
def update_dashboard_metrics(sender, instance, **kwargs):
    users = []
    """if sender == Transaction:
        users = [instance.client, instance.freelancer]"""
   """ if sender == Escrow:
        users = [instance.transaction.client, instance.transaction.freelancer]
    elif sender == EscrowDispute:
        users = [instance.escrow.transaction.client, instance.escrow.transaction.freelancer]"""
    if sender == Message:
        users = [instance.recipient]
    for user in users:
        if hasattr(user, 'dashboard'):
            user.dashboard.update_metrics()