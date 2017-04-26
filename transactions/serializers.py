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
        fields = ('id', 'due_date', 'description', 'category', 'value', 'kind', 'details', 'account')
        extra_kwargs = {
            'kind': {'read_only': True},
        }

    def get_kind(self):
        return self.context['kind']

    def validate_value(self, value):
        if self.context['kind'] == Transaction.EXPENSE_KIND:
            if value > 0:
                raise serializers.ValidationError('Expense value cannot be positive')
        elif value < 0:
            raise serializers.ValidationError('Income value cannot be negative')

        return value