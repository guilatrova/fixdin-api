from django.conf.urls import url
from integrations import views

urlpatterns = [
    url(r'^$', views.ListIntegrationsAPIView.as_view(), name="integrations"),
    url(r'^(?P<name_id>\w+)/$', views.IntegrationServiceAPIView.as_view(), name='integrations-service'),
    url(r'^(?P<name_id>\w+)/histories/$', views.ListIntegrationServiceHistoryAPIView.as_view(), name='integrations-service-histories'),
]