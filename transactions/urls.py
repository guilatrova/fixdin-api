from django.conf.urls import url
from transactions import views
from transactions.models import Category

category_list = views.CategoryCRUDViewSet.as_view({
    'get': 'list', 
    'post': 'create'
})

category_retrieve = views.CategoryCRUDViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

urlpatterns = [
    url(r'^expenses/$', category_list, name='expense-categories', kwargs={'kind': Category.EXPENSE_KIND}),
    url(r'^expenses/(?P<pk>\d+)$', category_retrieve, name='retrieve-expense-categories', kwargs={'kind': Category.EXPENSE_KIND})
]