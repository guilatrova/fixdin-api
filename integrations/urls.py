from django.conf.urls import url
from integrations import views

urlpatterns = [
    url(r'^integrations/$', views.ListIntegrations.as_view(), name="integrations"),
    # url(r'^values-by-category/(?P<kind>(expenses|incomes))/$', views.ValuesByCategoryAPIView.as_view(), name='values-by-category')
]