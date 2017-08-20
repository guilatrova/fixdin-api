from rest_framework import serializers
from transactions.serializers import TransactionSerializer

class Last13MonthsSerializer(serializers.Serializer):
    period = serializers.SerializerMethodField()
    date = serializers.DateField(write_only=True)    
    expenses = serializers.DecimalField(max_digits=20, decimal_places=2)
    incomes = serializers.DecimalField(max_digits=20, decimal_places=2)
    total = serializers.DecimalField(max_digits=20, decimal_places=2)

    def get_period(self, obj):        
        return '{}-{:02d}'.format(obj['date'].year, obj['date'].month)

class PendingSerializer(serializers.Serializer):
    overdue = TransactionSerializer(many=True, read_only=True)
    next = TransactionSerializer(many=True, read_only=True)