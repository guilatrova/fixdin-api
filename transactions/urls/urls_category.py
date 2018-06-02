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

category_list = views.CategoryViewSet.as_view(list_actions)
category_single = views.CategoryViewSet.as_view(single_action)

urlpatterns = [
    url(r'^$', category_list, name="categories"),
    url(r'^(?P<pk>\d+)$', category_single, name='category')    
]
