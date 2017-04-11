from django.conf.urls import url
from transactions import views
from transactions.models import Category

urlpatterns = [
    url(r'^expenses/', views.CategoryCRUDView.as_view({'get': 'list', 'post': 'create'}), name='expense-categories', kwargs={'kind': Category.EXPENSE_KIND}),
]