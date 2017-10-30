from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from integrations.models import Integration, IntegrationSettings, SyncHistory, CPFL_Settings
from integrations.serializers import IntegrationSerializer, SyncHistorySerializer, ServiceSettingsSerializer

class ListIntegrationsAPIView(ListAPIView):
    queryset = Integration.objects.all()
    serializer_class = IntegrationSerializer

class ListIntegrationServiceHistoryAPIView(ListAPIView):
    serializer_class = SyncHistorySerializer

    def get_queryset(self):
        return SyncHistory.objects.filter(
            settings__user=self.request.user,
            settings__integration__name_id=self.kwargs['name_id']
        )

class IntegrationSettingsAPIView(APIView):    

    def get(self, request, name_id, format='json'):
        factory = IntegrationSettingsViewFactory(name_id, request.user)
        serializer = factory.get_serializer()
        serializer.is_valid(raises_exception=True)
        return Response(serializer.data)

class IntegrationSettingsViewFactory:
    def __init__(self, name_id, user):
        self.name_id = name_id
        self.user = user

    def get_or_create_base_settings(self):
        return IntegrationSettings.objects.get_or_create(
            user=self.user,
            integration__name_id="cpfl",
            defaults={
                'integration': Integration.objects.get(name_id="cpfl")
            }
        )

    def get_data(self):
        base_setting, created = self.get_or_create_base_settings()
        cpfl_settings = CPFL_Settings.objects.filter(settings=base_setting)
        
        return base_setting, cpfl_settings

    def get_serializer(self):
        raw_base, raw_cpfl = self.get_data()
        data = {
            '',
            'cpfl_settings'
        }
        data['cpfl_settings'] = raw_cpfl
        ServiceSettingsSerializer(data)