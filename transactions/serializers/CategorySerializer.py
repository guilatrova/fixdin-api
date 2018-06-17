from rest_framework import serializers

from transactions.models import Category

from .HasKindContextSerializer import HasKindContextSerializer


class CategorySerializer(serializers.ModelSerializer, HasKindContextSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'kind')

    def validate_kind(self, value):
        if self.instance and self.instance.kind != value:
            raise serializers.ValidationError("Can't change kind")
        return value

    def validate(self, data):
        filters = {
            'user_id': self.context['user_id'],
            'name__iexact': data['name'],
            'kind': data['kind']
        }
        if Category.objects.filter(**filters).exists():
            raise serializers.ValidationError('Category already exists for this user with the same name and kind')

        return data
