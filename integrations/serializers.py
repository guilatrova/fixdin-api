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
    last_sync = serializers.DateField(required=False, allow_null=True, read_only=True)
    status = serializers.ChoiceField(choices=IntegrationSettings.STATUS, required=False, allow_null=True, read_only=True)

    def serialize_cpfl_settings(self):
        serializers = []
        for setting in self.validated_data['cpfl_settings']:
            serializer = CPFLSettingsSerializer(data=setting)
            serializer.is_valid(raise_exception=True)
            serializers.append(serializer)

        return serializers

    def save(self, integration):
        integration.enabled = self.validated_data['enabled']
        cpfl_serializers = self.serialize_cpfl_settings()
        for serializer in cpfl_serializers:
            # try:
                # instance = CPFL_Settings.objects.get(pk=serializer['id'])
                # CPFLSettingsSerializer()
            # except CPFL_Settings.DoesNotExist:
            serializer.save(settings=integration)


