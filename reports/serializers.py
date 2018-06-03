from rest_framework import serializers

from transactions.serializers import TransactionSerializer


class LastMonthsSerializer(serializers.Serializer):
    period = serializers.SerializerMethodField()
    date = serializers.DateField(write_only=True)
    effective_expenses = serializers.DecimalField(max_digits=20, decimal_places=2)
    effective_incomes = serializers.DecimalField(max_digits=20, decimal_places=2)
    real_expenses = serializers.DecimalField(max_digits=20, decimal_places=2)
    real_incomes = serializers.DecimalField(max_digits=20, decimal_places=2)
    effective_total = serializers.DecimalField(max_digits=20, decimal_places=2)
    real_total = serializers.DecimalField(max_digits=20, decimal_places=2)

    def get_period(self, obj):
        return '{}-{:02d}'.format(obj['date'].year, obj['date'].month)


class PendingSerializer(serializers.Serializer):
    overdue = TransactionSerializer(many=True, read_only=True)
    next = TransactionSerializer(many=True, read_only=True)


class ValuesByCategorySerializer(serializers.Serializer):
    category_id = serializers.IntegerField()
    total = serializers.DecimalField(max_digits=20, decimal_places=2)
