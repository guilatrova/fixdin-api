from rest_framework import serializers

class PeriodicSerializer(serializers.Serializer):
    frequency = serializers.ChoiceField(['daily', 'weekly', 'monthly', 'yearly'])
    interval = serializers.IntegerField()
    until = serializers.DateField(required=False)
    how_many = serializers.IntegerField(required=False)

    def validate_how_many(self, value):
        if value < 1:
            raise serializers.ValidationError('How many should be greater than 1')
        return value

    def validate(self, data):
        if 'how_many' not in data and 'until' not in data:
            raise serializers.ValidationError('You need to specify until when or how many times it should be repeated')

        if 'how_many' in data and 'until' in data:
            raise serializers.ValidationError('You cant specify both "how_many" and "until", not sure about how to repeat')

        return data