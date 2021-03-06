from django.db import transaction as db_transaction
from rest_framework import serializers

from transactions.factories import create_transfer_between_accounts, map_transaction_to_transfer_data
from transactions.models import Account, HasKind


def validate_account(id, user_id):
    if not Account.objects.filter(pk=id).exists():
        raise serializers.ValidationError('Invalid account id "{0}"'.format(id))

    account = Account.objects.get(pk=id)
    if account.user.id != user_id:
        raise serializers.ValidationError('This account does not belongs to you')
    
class TransferSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    account_from = serializers.IntegerField(required=False)
    account_to = serializers.IntegerField(required=False)
    value = serializers.DecimalField(max_digits=19, decimal_places=2)

    def validate_account_from(self, value):
        validate_account(value, self.context['user_id'])
        return value

    def validate_account_to(self, value):
        validate_account(value, self.context['user_id'])
        return value

    def validate_value(self, value):
        if self.context['request_method'] in ['POST', 'PUT']:
            if value < 0:
                raise serializers.ValidationError('Value should be greater than 0')

        return value

    def validate(self, data):
        if self.context['request_method'] == 'PUT':
            if 'account_from' in data or 'account_to' in data:
                raise serializers.ValidationError('You cant update accounts in transfer. Instead delete and create another')

        elif self.context['request_method'] == 'POST':
            if 'account_from' not in data or 'account_to' not in data:
                raise serializers.ValidationError('accounts must be set')
                
            if data['account_from'] == data['account_to']:
                raise serializers.ValidationError('You cant perform a transfer from and to same account')

        return data

    def create(self, validated_data):
        expense, income = create_transfer_between_accounts(self.context['user_id'], **validated_data)
        return map_transaction_to_transfer_data(expense)

    @db_transaction.atomic
    def update(self, expense, validated_data):
        assert expense.kind == HasKind.EXPENSE_KIND
        income = expense.bound_transaction

        expense.value = -validated_data['value']
        income.value = validated_data['value']
        
        expense.save()
        income.save()

        return map_transaction_to_transfer_data(expense)
