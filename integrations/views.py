from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from integrations import models
from integrations.serializers import IntegrationSerializer

class ListIntegrationsAPIView(ListAPIView):
    queryset = models.Integration.objects.all()
    serializer_class = IntegrationSerializer

class IntegrationServiceAPIView(APIView):
    pass