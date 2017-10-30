from rest_framework import serializers
from integrations.models import Integration, SyncHistory, IntegrationSettings, CPFL_Settings

class IntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Integration
        fields = '__all__'

class SyncHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncHistory
        fields = '__all__'

class CPFLSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CPFL_Settings
        fields = ('id', 'name', 'documento', 'imovel')

class ServiceSettingsSerializer(serializers.Serializer):
    cpfl_settings = CPFLSettingsSerializer(many=True)
    enabled = serializers.BooleanField()
    last_sync = serializers.DateField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=IntegrationSettings.STATUS, required=False, allow_null=True)