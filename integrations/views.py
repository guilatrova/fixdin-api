from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from integrations.models import Integration, SyncHistory
from integrations.serializers import IntegrationSerializer, SyncHistorySerializer

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

class IntegrationServiceAPIView(APIView):
    pass