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
        factory = IntegrationSettingsHandler(name_id, request.user)
        serializer = factory.retrieve_data()
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

    def put(self, request, name_id, format='json'):
        factory = IntegrationSettingsHandler(name_id, request.user)
        integration_instance, created = factory.get_or_create_base_settings()
        serializer_cls = factory.get_serializer()

        serializer = serializer_cls(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(integration_instance)
        
        return Response(serializer.data)


class IntegrationSettingsHandler:
    def __init__(self, name_id, user):
        self.name_id = name_id
        self.user = user

    def get_or_create_base_settings(self):
        return IntegrationSettings.objects.get_or_create(
            user=self.user,
            integration__name_id=self.name_id,
            defaults={
                'integration': Integration.objects.get(name_id=self.name_id)
            }
        )

    def retrieve_data(self):
        raw_base, created = self.get_or_create_base_settings()
        raw_cpfl = CPFL_Settings.objects.filter(settings=raw_base)
        
        cpfl = []
        for raw in raw_cpfl:
            cpfl.append({
                'id': raw.id,
                'name': raw.name,
                'documento': raw.documento,
                'imovel': raw.imovel
            })

        data = {
            'last_sync': raw_base.last_sync,
            'status': raw_base.status,
            'enabled': raw_base.enabled,
            'cpfl_settings': cpfl
        }

        return ServiceSettingsSerializer(data=data)

    def get_serializer(self):
        return ServiceSettingsSerializer
        