from rest_framework import viewsets

from transactions.models import Account
from transactions.serializers import AccountSerializer


class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer

    def get_queryset(self):
        return Account.objects.filter(user_id=self.request.user.id)

    def get_serializer_context(self):
        return {
            "user_id": self.request.user.id,
            "request_method": self.request.method
        }

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, current_effective_balance=0, current_real_balance=0)
