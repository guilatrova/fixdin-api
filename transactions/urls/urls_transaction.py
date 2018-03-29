from django.conf.urls import url
from transactions import views

list_actions = {
    'get': 'list'
}

retrieve_actions = {
    'get': 'retrieve'
}

urlpatterns = [
    url(r'^$', views.GenericTransactionAPIView.as_view(list_actions), name='transactions'),
    url(r'^(?P<pk>\d+)$', views.GenericTransactionAPIView.as_view(retrieve_actions), name='transaction'),
    url(r'^oldest-pending-expense/$', views.OldestPendingExpenseAPIView.as_view(), name='oldest-pending-expense')
]