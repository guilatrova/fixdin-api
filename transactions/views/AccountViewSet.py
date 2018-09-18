from rest_framework import status, viewsets
from rest_framework.response import Response

from transactions.filters import AccountFilter
from transactions.models import Account, Category, Transaction
from transactions.serializers import AccountSerializer


class AccountViewSet(viewsets.ModelViewSet, AccountFilter):
    serializer_class = AccountSerializer

    def get_queryset(self):
        query_filter = {
            'user_id': self.request.user.id,
        }
        filters = self.get_query_params_filter()

        query_filter.update(filters)
        return Account.objects.filter(**query_filter)

    def get_serializer_context(self):
        return {
            "id": self.kwargs.get('pk', None),
            "user_id": self.request.user.id,
            "request_method": self.request.method
        }

    def destroy(self, request, *args, **kwargs):
        if Transaction.objects.filter(account_id=kwargs['pk']).exclude(category__kind=Category.SYSTEM_KIND).exists():
            error_msg = 'Some transactions are bound to this account. Try archiving it instead.'
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'detail': error_msg})

        return super(AccountViewSet, self).destroy(self, request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, current_effective_balance=0, current_real_balance=0)
