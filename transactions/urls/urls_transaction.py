from django.conf.urls import url

from transactions import views

list_actions = {
    'get': 'list', 
    'post': 'create',
    'delete': 'destroy_all_periodics',
    'patch': 'partial_update_list',
}

single_action = {
    'get': 'retrieve',
    'put': 'update',
    'delete': 'destroy',
    'patch': 'partial_update',
}

transaction_list = views.TransactionViewSet.as_view(list_actions)
transaction_single = views.TransactionViewSet.as_view(single_action)

urlpatterns = [
    url(r'^$', transaction_list, name='transactions'),
    url(r'^(?P<pk>\d+)$', transaction_single, name='transaction'),
    url(r'^oldest-pending-expense/$', views.OldestPendingExpenseAPIView.as_view(), name='oldest-pending-expense')
]
