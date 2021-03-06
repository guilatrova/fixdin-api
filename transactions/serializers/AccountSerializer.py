from rest_framework import serializers

from balances.services import calculator
from transactions.models import Account


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('id', 'name', 'avatar', 'current_effective_balance', 'start_balance',
                  'current_real_balance', 'current_balance', 'status')
        read_only_fields = ('id', 'current_effective_balance', 'current_real_balance', 'current_balance')

    current_balance = serializers.SerializerMethodField()

    def get_current_balance(self, obj):
        return calculator.calculate_account_current_balance(obj.id)['real']

    def validate_name(self, value):
        ignores_itself = Account.objects.exclude(id=self.context.get("id", 0))
        if ignores_itself.filter(name__iexact=value, user_id=self.context['user_id']).exists():
            raise serializers.ValidationError('Account with that name already exists')

        return value
