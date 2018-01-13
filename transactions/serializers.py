from rest_framework import serializers
from transactions.models import Category, Transaction, Account
from transactions.factories import create_periodic_transactions
from rest_framework.utils.serializer_helpers import ReturnDict, ReturnList

class HasKindContextSerializer():
    def get_kind(self, obj):
        return self.context['kind']

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('id', 'name', 'current_balance')
        read_only_fields = ('id', 'current_balance', )

    def validate_name(self, value):
        if Account.objects.filter(name__iexact=value, user_id=self.context['user_id']).exists():
            raise serializers.ValidationError('Account with that name already exists')

        return value

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
    frequency = serializers.ChoiceField(['daily', 'weekly', 'monthly', 'yearly'])
    interval = serializers.IntegerField()
    until = serializers.DateField(required=False)
    how_many = serializers.IntegerField(required=False)

    def validate_how_many(self, value):
        if value < 1:
            raise serializers.ValidationError('How many should be greater than 1')
        return value

    def validate(self, data):
        if 'how_many' not in data and 'until' not in data:
            raise serializers.ValidationError('You need to specify until when or how many times it should be repeated')

        if 'how_many' in data and 'until' in data:
            raise serializers.ValidationError('You cant specify both "how_many" and "until", not sure about how to repeat')

        return data

class TransactionSerializer(serializers.ModelSerializer, HasKindContextSerializer):
    class Meta:
        model = Transaction
        fields = ('id', 'due_date', 'description', 'category', 'value', 'kind', 'details', 'account', 'priority', 'deadline', 'payment_date', 'periodic', 'bound_transaction', 'bound_reason')
        read_only_fields = ('kind', 'bound_transaction')
        write_only_fields = ('periodic',)

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

    def validate_periodic(self, periodic):
        if periodic is not None and self.context['request_method'] == 'PUT':
            raise serializers.ValidationError("You can't update a transaction to be periodic. Create a new one instead.")
        return periodic

    def validate(self, data):
        if 'periodic' in data and 'until' in data['periodic'] and data['periodic']['until'] < data['due_date']:
            raise serializers.ValidationError("Periodic until must be greater than due date")

        if 'category' in data:
            if self.context['kind'] != data['category'].kind:
                raise serializers.ValidationError('Transaction and Category must have the same kind')
        return data

    def to_representation(self, value):
        if isinstance(value, list):
            return [super(TransactionSerializer, self).to_representation(x) for x in value]

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
            return super(TransactionSerializer, self).create(validated_data)

        return create_periodic_transactions(**validated_data)