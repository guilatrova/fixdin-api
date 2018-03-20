from rest_framework import serializers
from transactions.models import Transaction
from transactions import factories
from rest_framework.utils.serializer_helpers import ReturnDict, ReturnList
from .PeriodicSerializer import PeriodicSerializer
from .HasKindContextSerializer import HasKindContextSerializer
from common.serializers import SerializerMayReturnListMixin

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