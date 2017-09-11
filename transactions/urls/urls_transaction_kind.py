from django.conf.urls import url
from transactions import views
from transactions.models import Category

list_actions = {
    'get': 'list', 
    'post': 'create',
    'delete': 'destroy_all_periodics'
}

single_action = {
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
}

transaction_list = views.TransactionViewSet.as_view(list_actions)
transaction_single = views.TransactionViewSet.as_view(single_action)

urlpatterns = [
    url(r'^$', transaction_list, name='kind_transactions'),
    url(r'^(?P<pk>\d+)$', transaction_single, name='kind_transaction'),
]