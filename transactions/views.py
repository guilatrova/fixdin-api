from datetime import datetime
from django.http import Http404
from django.db.models import Q
from django.shortcuts import render
from django.db import transaction as db_transaction
from rest_framework import viewsets, status, mixins, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from transactions.models import Category, Transaction, Account, BoundReasons, HasKind
from transactions.filters import TransactionFilter
from transactions.serializers import CategorySerializer, TransactionSerializer, AccountSerializer,  TransferSerializer
from transactions.factories import map_queryset_to_serializer_data, map_transaction_to_transfer_data

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
        serializer.save(user=self.request.user, current_balance=0)

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.filter(kind=self.kwargs['kind'], user_id=self.request.user.id)

    def get_serializer_context(self):
        return {
            "user_id": self.request.user.id,
            "kind": self.kwargs['kind']
        }

    def destroy(self, request, *args, **kwargs):
        if Transaction.objects.filter(category_id=kwargs['pk']).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'detail': 'Some transactions are using this category'})

        return super(CategoryViewSet, self).destroy(self, request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, kind=self.kwargs['kind'])

class TransactionViewSet(viewsets.ModelViewSet, TransactionFilter):
    '''
    Handles /expenses and /incomes endpoints
    '''
    serializer_class = TransactionSerializer

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
    
    def update(self, request, *args, **kwargs):
        if request.query_params.get('next', False) == '1':
            instance = self.get_object()
            next_periodics = Transaction.objects.filter(bound_transaction=instance.bound_transaction, due_date__gte=instance.due_date).order_by('id')
            to_return = self._patch_periodics(request.data, next_periodics)

            return Response(to_return)
        else:
            return super(TransactionViewSet, self).update(request, *args, **kwargs)

    def patch_list(self, request, *args, **kwargs):
        periodic = self.request.query_params.get('periodic_transaction', False)
        if periodic:
            queryset = self.filter_queryset(Transaction.objects.filter(bound_transaction=periodic)).order_by('id')
            to_return = self._patch_periodics(request.data, queryset)

            return Response(to_return)
        
        transactions = self.request.query_params.get('ids', False)
        if transactions:
            ids = transactions.split(',')
            queryset = self.filter_queryset(Transaction.objects.filter(id__in=ids))
            to_return = self._patch_list(request.data, queryset)

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

            if is_first:
                data.pop('due_date', None)
                data.pop('payment_date', None)
                is_first = False

        return to_return

    def _patch_list(self, data, transactions):
        to_return = []

        for instance in transactions:
            serializer = self.get_serializer(instance, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            to_return.append(serializer.data)

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
            return super(TransactionViewSet, self).perform_destroy(instance)

    def perform_create(self, serializer):
        serializer.save(kind=self.kwargs['kind'])

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

    def get_object(self, pk):
        try:
            obj = Transaction.objects.get(\
                Q(id=pk) | Q(bound_transaction_id=pk),
                Q(account__user_id=self.request.user.id),
                Q(bound_reason=BoundReasons.TRANSFER_BETWEEN_ACCOUNTS),
                Q(kind=HasKind.EXPENSE_KIND)
            )
        except Transaction.DoesNotExist:
            raise Http404('No %s matches the given query.' % queryset.model._meta.object_name)
        
        self.check_object_permissions(self.request, obj)

        return obj

    def get_serializer_context(self):
        return {
            'user_id': self.request.user.id
        }    

    def list(self, request):
        queryset = self.get_queryset()        
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
