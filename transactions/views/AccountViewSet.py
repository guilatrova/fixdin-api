from rest_framework import viewsets

from transactions.filters import AccountFilter
from transactions.models import Account
from transactions.serializers import AccountSerializer


class AccountViewSet(viewsets.ModelViewSet, AccountFilter):
    serializer_class = AccountSerializer

    def get_queryset(self):
        query_filter = {
            'user_id': self.request.user.id,
        }
        filters = self.get_query_params_filter()

        query_filter.update(filters)
        return Account.objects.filter(**filters)

    def get_serializer_context(self):
        return {
            "user_id": self.request.user.id,
            "request_method": self.request.method
        }

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, current_effective_balance=0, current_real_balance=0)
