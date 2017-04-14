from django.shortcuts import render
from rest_framework import viewsets
from transactions.models import Category
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

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, kind=self.kwargs['kind'])

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
