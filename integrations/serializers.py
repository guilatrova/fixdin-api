from rest_framework import serializers
from integrations.models import Integration

class IntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Integration
        fields = ('name_id', 'name')