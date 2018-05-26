from django.http import Http404
from rest_framework import viewsets, mixins, generics
from rest_framework.response import Response
from transactions.models import Transaction
from transactions.filters import TransactionFilter
from transactions.serializers import TransactionSerializer

class OldestPendingExpenseAPIView(generics.RetrieveAPIView):
    serializer_class = TransactionSerializer

    def get_object(self):
        obj = self.get_queryset()
        if obj is None:
            raise Http404()
        return obj

    def get_queryset(self):
        return Transaction.objects\
            .owned_by(self.request.user.id)\
            .pending()\
            .expenses()\
            .order_by('due_date')\
            .first()
