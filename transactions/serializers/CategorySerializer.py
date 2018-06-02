from rest_framework import serializers
from transactions.models import Category

from .HasKindContextSerializer import HasKindContextSerializer


class CategorySerializer(serializers.ModelSerializer, HasKindContextSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'kind')

    def validate(self, data):
        if Category.objects.filter(name__iexact=data['name'],user_id=self.context['user_id'],kind=data['kind']).exists():
            raise serializers.ValidationError('Category already exists for this user with the same name and kind')

        return data
