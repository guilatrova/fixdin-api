from rest_framework import serializers
from transactions.models import Account

def validate_account(id):
    if not Account.objects.filter(pk=id).exists():
        raise serializers.ValidationError('Invalid account id "{0}"'.format(id))

    # User is owner
    
class TransferSerializer(serializers.Serializer):
    account_from = serializers.IntegerField()
    account_to = serializers.IntegerField()
    value = serializers.DecimalField(max_digits=19, decimal_places=2)

    def validate_account_from(self, value):
        validate_account(value)
        return value

    def validate_account_to(self, value):
        validate_account(value)
        return value

    def validate(self, data):
        if data['account_from'] == data['account_to']:
            raise serializers.ValidationError('You cant perform a transfer from and to same account')

        return data