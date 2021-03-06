from rest_framework import serializers

from transactions.models import Category

from .HasKindContextSerializer import HasKindContextSerializer


class CategorySerializer(serializers.ModelSerializer, HasKindContextSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'kind')

    def validate_name(self, name):
        if name.endswith("_sys"):
            raise serializers.ValidationError("You can't use that name")
        return name

    def validate(self, data):
        filters = {
            'user_id': self.context['user_id'],
            'name__iexact': data['name'],
            'kind': data['kind']
        }
        if Category.objects.filter(**filters).exists():
            raise serializers.ValidationError('Category already exists for this user with the same name and kind')

        return data
