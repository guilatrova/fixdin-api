from django.shortcuts import render
from rest_framework import viewsets
from transactions.models import Category
from transactions.serializers import CategorySerializer

class CategoryCRUDViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all() #TODO: filter by user and kind
    serializer_class = CategorySerializer

    # def get_queryset(self):
    #     return Profile.objects.filter(pk=self.request.user.profile.id)

    def get_serializer_context(self):
        return {
            "user_id": self.request.user.id,
            "kind": self.kwargs['kind']
        }

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, kind=self.kwargs['kind'])