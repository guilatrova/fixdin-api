from rest_framework import status, viewsets
from rest_framework.response import Response

from transactions.models import Category, Transaction
from transactions.serializers import CategorySerializer


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer

    def get_queryset(self):
        filters = {}        
        kind = self.request.query_params.get('kind', False)
        if kind:
            filters['kind'] = kind

        return Category.objects.filter(user_id=self.request.user.id, **filters)

    def get_serializer_context(self):
        return { "user_id": self.request.user.id }

    def destroy(self, request, *args, **kwargs):
        if Transaction.objects.filter(category_id=kwargs['pk']).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'detail': 'Some transactions are using this category'})

        return super(CategoryViewSet, self).destroy(self, request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
