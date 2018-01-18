from rest_framework import serializers
from transactions.models import Account

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('id', 'name', 'current_balance')
        read_only_fields = ('id', 'current_balance', )

    def validate_name(self, value):
        if Account.objects.filter(name__iexact=value, user_id=self.context['user_id']).exists():
            raise serializers.ValidationError('Account with that name already exists')

        return value
