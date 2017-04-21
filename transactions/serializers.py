from rest_framework import serializers
from transactions.models import Category, Transaction

class CategorySerializer(serializers.ModelSerializer):
    kind = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'name', 'kind')

    def validate_name(self, value):
        if Category.objects.filter(name__iexact=value,user_id=self.context['user_id']).exists():
            raise serializers.ValidationError('Category already exists for this user')

        return value

    def get_kind(self, obj):
        return self.context['kind']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ('id', 'due_date', 'description', 'category', 'value', 'payed', 'details', 'account')

    def validate_value(self, value):
        if value == 0:
            raise serializers.ValidationError('Value cannot be 0')

        return value