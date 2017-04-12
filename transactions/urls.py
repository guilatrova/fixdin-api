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
    #expenses
    url(r'^expenses/$', category_list, name='expense-categories', kwargs={'kind': Category.EXPENSE_KIND}),
    url(r'^expenses/(?P<pk>\d+)$', category_retrieve, name='expense-category', kwargs={'kind': Category.EXPENSE_KIND}),

    #incomes
    url(r'^incomes/$', category_list, name='income-categories', kwargs={'kind': Category.INCOME_KIND}),
    url(r'^incomes/(?P<pk>\d+)$', category_retrieve, name='income-category', kwargs={'kind': Category.INCOME_KIND})
]