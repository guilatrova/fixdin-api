from django.conf.urls import url

from transactions import views
from transactions.models import Category

list_actions = {
    'get': 'list', 
    'post': 'create'
}

single_action = {
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
}

urlpatterns = [
    url(r'^$', views.CategoryViewSet.as_view(list_actions), name="categories"),
    url(r'^(?P<pk>\d+)$', views.CategoryViewSet.as_view(single_action), name="category")
]
