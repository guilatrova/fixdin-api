# from django.conf.urls import url
# from transactions import views
# from transactions.models import Category

# list_actions = {
#     'get': 'list', 
#     'post': 'create'
# }

# single_action = {
#     'get': 'retrieve',
#     'put': 'update',
#     'patch': 'partial_update',
#     'delete': 'destroy'
# }

# category_list = views.CategoryViewSet.as_view(list_actions)
# category_single = views.CategoryViewSet.as_view(single_action)
# transaction_list = views.TransactionViewSet.as_view(list_actions)
# transaction_single = views.TransactionViewSet.as_view(single_action)

# urlpatterns = [
#     ##TRANSACTIONS
#     #expenses
#     url(r'^$', transaction_list, name='expenses'),
#     url(r'^(?P<pk>\d+)$', transaction_single, name='expense'),
    
#     ##CATEGORIES
#     #expenses
#     url(r'^expenses/$', category_list, name='expense-categories', kwargs={'kind': Category.EXPENSE_KIND}),
#     url(r'^expenses/(?P<pk>\d+)$', category_single, name='expense-category', kwargs={'kind': Category.EXPENSE_KIND}),
#     #incomes
#     url(r'^incomes/$', category_list, name='income-categories', kwargs={'kind': Category.INCOME_KIND}),
#     url(r'^incomes/(?P<pk>\d+)$', category_single, name='income-category', kwargs={'kind': Category.INCOME_KIND}),    
# ]