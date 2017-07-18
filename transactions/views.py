from django.shortcuts import render
from django.db.models import Sum
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from transactions.models import Category, Transaction, Account
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

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        query_filter = { 
            'account__user_id': self.request.user.id,
            'kind': self.kwargs['kind'] 
            }
        
        url_query_params = self.get_query_params_filter()  
        query_filter.update(url_query_params)
        return Transaction.objects.filter(**query_filter)

    def get_query_params_filter(self):
        dic = {}
        fields = ['due_date', 'category']

        for field in fields:
            value = self.request.query_params.get(field, None)
            if value is not None:
                dic[field] = value

        return dic

    def get_serializer_context(self):
        return {
            "kind": self.kwargs['kind'],
            "user_id": self.request.user.id
        }

    def perform_create(self, serializer):
        account = Account.objects.filter(user_id=self.request.user.id).first()
        serializer.save(kind=self.kwargs['kind'],account=account)

class BalanceAPIView(APIView):

    def get(self, request, format='json'):
        total_sum = Transaction.objects.filter(account__user_id=request.user.id).aggregate(Sum('value'))['value__sum']
        return Response({ 'balance': total_sum })