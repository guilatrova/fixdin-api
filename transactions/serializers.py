from rest_framework import serializers
from transactions.models import Category

class CategorySerializer(serializers.ModelSerializer):
    kind = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'name', 'kind')

    def get_kind(self, obj):
        return self.context['kind']