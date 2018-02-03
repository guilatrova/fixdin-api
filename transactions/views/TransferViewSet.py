from django.http import Http404
from django.db import transaction as db_transaction
from django.db.models import Q
from rest_framework import viewsets, status, mixins, generics
from rest_framework.response import Response
from transactions.models import Transaction, BoundReasons, HasKind
from transactions.serializers import TransferSerializer
from transactions.factories import map_queryset_to_serializer_data, map_transaction_to_transfer_data

class TransferViewSet(viewsets.ViewSet, mixins.CreateModelMixin, generics.GenericAPIView):
    """
    Handles CRUD operations for specific transactions: 
    transfers between accounts.
    """
    serializer_class = TransferSerializer

    def get_queryset(self):
        return Transaction.objects.filter(\
            account__user_id=self.request.user.id,
            bound_reason=BoundReasons.TRANSFER_BETWEEN_ACCOUNTS,
            kind=HasKind.EXPENSE_KIND) # Get just one of pair (from)

    def get_object(self, pk=None):
        try:
            obj = Transaction.objects.get(\
                Q(id=pk) | Q(bound_transaction_id=pk),
                Q(account__user_id=self.request.user.id), # TO DO: User permission instead
                Q(bound_reason=BoundReasons.TRANSFER_BETWEEN_ACCOUNTS),
                Q(kind=HasKind.EXPENSE_KIND)
            )
        except Transaction.DoesNotExist:
            raise Http404('No %s matches the given query.' % queryset.model._meta.object_name)
        
        self.check_object_permissions(self.request, obj)

        return obj

    def get_serializer_context(self):
        return {
            'user_id': self.request.user.id,
            "request_method": self.request.method
        }    

    def list(self, request):
        queryset = self.get_queryset()        
        data = map_queryset_to_serializer_data(queryset)
        serializer = self.get_serializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

    def list_from_account(self, request, pk):
        queryset = self.get_queryset().filter(Q(account_id=pk) | Q(bound_transaction__account_id=pk))
        data = map_queryset_to_serializer_data(queryset)
        serializer = self.get_serializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
        
    def retrieve(self, request, pk=None):        
        instance = self.get_object(pk)
        data = map_transaction_to_transfer_data(instance)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

    def update(self, request, pk=None):
        instance = self.get_object(pk)
        
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @db_transaction.atomic
    def destroy(self, request, pk=None):
        instance = self.get_object(pk)
        instance.bound_transaction.delete()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)