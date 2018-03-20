from rest_framework import viewsets, mixins, generics
from rest_framework.response import Response
from transactions.models import Transaction
from transactions.filters import TransactionFilter
from transactions.serializers import TransactionSerializer

class GenericTransactionAPIView(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet, TransactionFilter):
    '''
    Handles only GET to retrieve all transactions
    '''
    serializer_class = TransactionSerializer

    def get_queryset(self):
        query_filter = { 
            'account__user_id': self.request.user.id,
        }
        
        url_query_params = self.get_query_params_filter()  
        query_filter.update(url_query_params)
        return Transaction.objects.filter(**query_filter)

class OldestPendingExpenseAPIView(generics.RetrieveAPIView):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return Transaction.objects\
            .owned_by(request.user.id)\
            .pending()\
            .expenses()\
            .order_by('due_date')\
            .first()
