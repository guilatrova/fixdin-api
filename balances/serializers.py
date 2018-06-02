from rest_framework import serializers


class PeriodSerializer(serializers.Serializer):
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
