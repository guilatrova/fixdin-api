from django.conf.urls import url
from transactions import views

list_actions = {
    'get': 'list'
}

retrieve_actions = {
    'get': 'retrieve'
}

urlpatterns = [
    url(r'^$', views.TransactionAPIView.as_view(list_actions), name='transactions'),
    url(r'^(?P<pk>\d+)$', views.TransactionAPIView.as_view(retrieve_actions), name='transaction'),
]