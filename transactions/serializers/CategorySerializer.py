from rest_framework import serializers
from transactions.models import Category
from .HasKindContextSerializer import HasKindContextSerializer

class CategorySerializer(serializers.ModelSerializer, HasKindContextSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'kind')
        read_only_fields = ('kind', )

    def validate_name(self, value):
        if Category.objects.filter(name__iexact=value,user_id=self.context['user_id'],kind=self.context['kind']).exists():
            raise serializers.ValidationError('Category already exists for this user with the same name and kind')

        return value