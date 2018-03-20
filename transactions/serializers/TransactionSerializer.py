from rest_framework import serializers
from transactions.models import Transaction
from transactions import factories
from rest_framework.utils.serializer_helpers import ReturnDict, ReturnList
from .PeriodicSerializer import PeriodicSerializer
from .HasKindContextSerializer import HasKindContextSerializer

class SerializerMayReturnListMixin:
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
        
        if hasattr(self, '_validated_data') and self.is_return_data_list(self._validated_data):
            return ReturnList(self._data, serializer=self)
        return ReturnDict(self._data, serializer=self)

    def to_representation(self, value):
        if isinstance(value, list):
            return [super(SerializerMayReturnListMixin, self).to_representation(x) for x in value]

        return super(SerializerMayReturnListMixin, self).to_representation(value)

class TransactionSerializer(SerializerMayReturnListMixin, serializers.ModelSerializer, HasKindContextSerializer):
    class Meta:
        model = Transaction
        fields = ('id', 'due_date', 'description', 'category', 'value', 'kind', 'details', 'account', 'priority', 'deadline', 'payment_date', 'periodic', 'bound_transaction', 'bound_reason')
        read_only_fields = ('kind', 'bound_transaction', 'bound_reason')
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

    def is_return_data_list(self, validated_data):
        return 'periodic' in validated_data    

    def create(self, validated_data):
        if 'periodic' in validated_data:            
            return factories.create_periodic_transactions(**validated_data)

        return super(TransactionSerializer, self).create(validated_data)