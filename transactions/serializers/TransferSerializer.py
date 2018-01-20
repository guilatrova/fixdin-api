from rest_framework import serializers
from transactions.models import Account
from transactions.factories import create_transfer_between_accounts, map_transaction_to_transfer_data

def validate_account(id, user_id):
    if not Account.objects.filter(pk=id).exists():
        raise serializers.ValidationError('Invalid account id "{0}"'.format(id))

    account = Account.objects.get(pk=id)
    if account.user.id != user_id:
        raise serializers.ValidationError('This account does not belongs to you')
    
class TransferSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    account_from = serializers.IntegerField()
    account_to = serializers.IntegerField()
    value = serializers.DecimalField(max_digits=19, decimal_places=2)

    def validate_account_from(self, value):
        validate_account(value, self.context['user_id'])
        return value

    def validate_account_to(self, value):
        validate_account(value, self.context['user_id'])
        return value

    def validate(self, data):
        if data['account_from'] == data['account_to']:
            raise serializers.ValidationError('You cant perform a transfer from and to same account')

        return data

    def create(self, validated_data):
        expense, income = create_transfer_between_accounts(self.context['user_id'], **validated_data)
        return map_transaction_to_transfer_data(expense)
