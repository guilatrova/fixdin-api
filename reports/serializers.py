from rest_framework import serializers

class Last13DaysSerializer(serializers.Serializer):
    period = serializers.SerializerMethodField()
    date = serializers.DateField(write_only=True)
    total = serializers.DecimalField(max_digits=20, decimal_places=2)

    def get_period(self, obj):        
        return '{}-{:02d}'.format(obj['date'].year, obj['date'].month)