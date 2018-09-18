from django.db import transaction as db_transaction
from django.db.models import F
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
        return {"user_id": self.request.user.id}

    def destroy(self, request, *args, **kwargs):
        if Transaction.objects.filter(category_id=kwargs['pk']).exists():
            data = {'detail': 'Some transactions are using this category'}
            return Response(status=status.HTTP_400_BAD_REQUEST, data=data)

        return super(CategoryViewSet, self).destroy(self, request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @db_transaction.atomic
    def perform_update(self, serializer):
        category = Category.objects.get(pk=self.kwargs['pk'])
        if serializer.validated_data['kind'] != category.kind:
            Transaction.objects\
                .filter(category_id=self.kwargs['pk'])\
                .update(
                    kind=serializer.validated_data['kind'],
                    value=F('value') * -1
                )

        serializer.save()
