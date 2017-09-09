from rest_framework import serializers
from transactions.models import Category, Transaction
from transactions.factories import create_periodic_transactions
from rest_framework.utils.serializer_helpers import ReturnDict, ReturnList

class HasKindContextSerializer():
    def get_kind(self, obj):
        return self.context['kind']

class CategorySerializer(serializers.ModelSerializer, HasKindContextSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'kind')
        read_only_fields = ('kind', )

    def validate_name(self, value):
        if Category.objects.filter(name__iexact=value,user_id=self.context['user_id'],kind=self.context['kind']).exists():
            raise serializers.ValidationError('Category already exists for this user with the same name and kind')

        return value

class PeriodicSerializer(serializers.Serializer):
    period = serializers.ChoiceField(['daily', 'weekly', 'monthly', 'yearly'])
    distance = serializers.IntegerField()
    until = serializers.DateField()

class TransactionSerializer(serializers.ModelSerializer, HasKindContextSerializer):
    class Meta:
        model = Transaction
        fields = ('id', 'due_date', 'description', 'category', 'value', 'kind', 'details', 'account', 'priority', 'deadline', 'payment_date', 'periodic')
        read_only_fields = ('kind', 'account')
        write_only_fields = ('periodic')

    periodic = PeriodicSerializer(required=False, write_only=True)

    def validate_value(self, value):
        if self.context['kind'] == Transaction.EXPENSE_KIND:
            if value > 0:
                raise serializers.ValidationError('Expense value cannot be positive')
        elif value < 0:
            raise serializers.ValidationError('Income value cannot be negative')

        return value

    def validate_category(self, category):
        if category.user.id != self.context['user_id']:
            raise serializers.ValidationError("You can't use a category that doesn't belongs to you!")
        return category

    def validate_account(self, account):
        if account.user.id != self.context['user_id']:
            raise serializers.ValidationError("You can't use an account that doesn't belongs to you!")
        return account

    def validate(self, data):
        if self.context['kind'] != data['category'].kind:
            raise serializers.ValidationError('Transaction and Category must have the same kind')
        return data

    def to_representation(self, value):
        if isinstance(value, list):
            result = []
            for x in value:
                result.append(super(TransactionSerializer, self).to_representation(x))
            return result

        return super(TransactionSerializer, self).to_representation(value)

    @property
    def data(self):
        if hasattr(self, 'initial_data') and not hasattr(self, '_validated_data'):
            msg = (
                'When a serializer is passed a `data` keyword argument you '
                'must call `.is_valid()` before attempting to access the '
                'serialized `.data` representation.\n'
                'You should either call `.is_valid()` first, '
                'or access `.initial_data` instead.'
            )
            raise AssertionError(msg)

        if not hasattr(self, '_data'):
            if self.instance is not None and not getattr(self, '_errors', None):
                self._data = self.to_representation(self.instance)
            elif hasattr(self, '_validated_data') and not getattr(self, '_errors', None):
                self._data = self.to_representation(self.validated_data)
            else:
                self._data = self.get_initial()        
        
        if hasattr(self, '_validated_data') and 'periodic' in self._validated_data:
            return ReturnList(self._data, serializer=self)
        return ReturnDict(self._data, serializer=self)

    def create(self, validated_data):
        if 'periodic' not in validated_data:
            return super().create(validated_data)

        transactions = create_periodic_transactions(**validated_data)
        return transactions
