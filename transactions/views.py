from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from transactions.models import Category, Transaction
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
        return Transaction.objects.filter(account__user_id=self.request.user.id)

    def get_serializer_context(self):
        return {
            "kind": self.kwargs['kind']
        }