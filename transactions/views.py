from datetime import datetime
from django.shortcuts import render
from django.db import transaction as db_transaction
from rest_framework import viewsets, status, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from transactions.models import Category, Transaction, Account
from transactions.filters import TransactionFilter
from transactions.serializers import CategorySerializer, TransactionSerializer

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
    
    def patch_all_periodics(self, request, *args, **kwargs):
        periodic = self.request.query_params.get('periodic_transaction', False)
        if periodic:
            queryset = self.filter_queryset(Transaction.objects.filter(periodic_transaction=periodic))
            to_return = self.patch_periodics(request.data, queryset)

            return Response(to_return)

        return Response(status=status.HTTP_404_NOT_FOUND)
    
    def destroy_all_periodics(self, request, *args, **kwargs):
        periodic = self.request.query_params.get('periodic_transaction', False)
        if periodic:
            Transaction.objects.filter(periodic_transaction=periodic).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_404_NOT_FOUND)

    def update(self, request, *args, **kwargs):
        if request.query_params.get('next', False) == '1':
            instance = self.get_object()
            next_periodics = Transaction.objects.filter(periodic_transaction=instance.periodic_transaction, due_date__gte=instance.due_date)
            to_return = self.patch_periodics(request.data, next_periodics)

            return Response(to_return)
        else:
            return super(TransactionViewSet, self).update(request, *args, **kwargs)

    @db_transaction.atomic
    def patch_periodics(self, data, periodics):
        to_return = []

        for instance in periodics:
            serializer = self.get_serializer(instance, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            to_return.append(serializer.data)

        return to_return

    def perform_destroy(self, instance):
        params = self.request.query_params

        if params.get('next', False) == '1':
            Transaction.objects.filter(periodic_transaction=instance.periodic_transaction, due_date__gte=instance.due_date).delete()
        else:
            return super(TransactionViewSet, self).perform_destroy(instance)

    def perform_create(self, serializer):
        account = Account.objects.filter(user_id=self.request.user.id).first()
        serializer.save(kind=self.kwargs['kind'],account=account)

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