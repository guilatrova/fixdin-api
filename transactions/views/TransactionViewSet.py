from django.db import transaction as db_transaction
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from transactions.models import Transaction
from transactions.filters import TransactionFilter
from transactions.serializers import TransactionSerializer
from transactions.permissions import IsNotTransferOrIsReadOnly

class PeriodicTransactionViewSetMixin:
    '''
    Mixin that injects handlers for PUT/PATCH/DELETE periodic transactions
    '''
    def update(self, request, *args, **kwargs):
        if request.query_params.get('next', False) == '1':
            instance = self.get_object()
            next_periodics = Transaction.objects.filter(bound_transaction=instance.bound_transaction, due_date__gte=instance.due_date).order_by('id')
            to_return = self._patch_periodics(request.data, next_periodics)

            return Response(to_return)
        else:
            return super(PeriodicTransactionViewSetMixin, self).update(request, *args, **kwargs)

    def partial_update_list(self, request, *args, **kwargs):
        periodic = self.request.query_params.get('periodic_transaction', False)
        if periodic: #TODO: CHECK FILTER WORKS CORRECTLY
            queryset = self.filter_queryset(Transaction.objects.filter(bound_transaction=periodic)).order_by('due_date')
            to_return = self._patch_periodics(request.data, queryset)

            return Response(to_return)

        return Response(status=status.HTTP_404_NOT_FOUND)

    @db_transaction.atomic
    def _patch_periodics(self, data, periodics):
        to_return = []        

        is_first = True
        for instance in periodics:
            serializer = self.get_serializer(instance, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            to_return.append(serializer.data)

            if is_first: #TODO: Move it from here + Test it
                data.pop('due_date', None)
                data.pop('payment_date', None)
                is_first = False

        return to_return

    def destroy_all_periodics(self, request, *args, **kwargs):
        periodic = self.request.query_params.get('periodic_transaction', False)
        if periodic:
            Transaction.objects.filter(bound_transaction=periodic).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_404_NOT_FOUND)

    def perform_destroy(self, instance):
        params = self.request.query_params

        if params.get('next', False) == '1':
            Transaction.objects.filter(bound_transaction=instance.bound_transaction, due_date__gte=instance.due_date).delete()
        else:
            return super(PeriodicTransactionViewSetMixin, self).perform_destroy(instance)

class TransactionViewSet(PeriodicTransactionViewSetMixin, viewsets.ModelViewSet, TransactionFilter):
    '''
    Handles /expenses and /incomes endpoints
    '''
    serializer_class = TransactionSerializer
    permission_classes = (IsAuthenticated, IsNotTransferOrIsReadOnly)

    def get_serializer_context(self):
        return {
            "kind": self.kwargs['kind'],
            "user_id": self.request.user.id,
            "request_method": self.request.method
        }

    def get_queryset(self):
        query_filter = { 
            'account__user_id': self.request.user.id,
            'kind': self.kwargs['kind'] 
        }
        
        url_query_params = self.get_query_params_filter()  
        query_filter.update(url_query_params)
        return Transaction.objects.filter(**query_filter)

    def partial_update_list(self, request, *args, **kwargs):
        transactions = self.request.query_params.get('ids', False)
        if transactions:
            ids = transactions.split(',')
            queryset = self.filter_queryset(Transaction.objects.filter(id__in=ids))
            to_return = self._patch_list(request.data, queryset)

            return Response(to_return)        
        
        #TODO: CREATE A MIXIN FOR VIEWSET TO HANDLE PARTIAL_UPDATE_LIST
        return super().partial_update_list(request, *args, **kwargs)

    def _patch_list(self, data, transactions):
        to_return = []

        for instance in transactions:
            serializer = self.get_serializer(instance, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            to_return.append(serializer.data)

        return to_return

    def perform_create(self, serializer):
        serializer.save(kind=self.kwargs['kind'])

