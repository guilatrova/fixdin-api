from rest_framework import serializers
from transactions.models import Category, Transaction

class HasKindContextSerializer():
    def get_kind(self, obj):
        return self.context['kind']

class CategorySerializer(serializers.ModelSerializer, HasKindContextSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'kind')
        read_only_fields = ('kind', )

    def validate_name(self, value):
        if Category.objects.filter(name__iexact=value,user_id=self.context['user_id']).exists():
            raise serializers.ValidationError('Category already exists for this user')

        return value

class TransactionSerializer(serializers.ModelSerializer, HasKindContextSerializer):
    class Meta:
        model = Transaction
        fields = ('id', 'due_date', 'description', 'category', 'value', 'kind', 'details', 'account', 'priority', 'deadline')
        read_only_fields = ('kind', )

    def validate_value(self, value):
        if self.context['kind'] == Transaction.EXPENSE_KIND:
            if value > 0:
                raise serializers.ValidationError('Expense value cannot be positive')
        elif value < 0:
            raise serializers.ValidationError('Income value cannot be negative')

        return value