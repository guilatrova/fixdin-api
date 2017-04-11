from django.shortcuts import render
from rest_framework import viewsets
from transactions.models import Category
from transactions.serializers import CategorySerializer

class CategoryCRUDView(viewsets.ModelViewSet):
    queryset = Category.objects.all() #TODO: filter by user and kind
    serializer_class = CategorySerializer

    def get_serializer_context(self):
        return {
            "user_id": self.request.user.id,
            "kind": self.kwargs['kind']
        }

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, kind=self.kwargs['kind'])