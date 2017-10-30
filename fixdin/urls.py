"""fixdin URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from transactions.models import Transaction

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/v1/auth/', include('users.urls')),
    url(r'^api/v1/balances/', include('balances.urls')),
    url(r'^api/v1/reports/', include('reports.urls')),
    url(r'^api/v1/integrations/', include('integrations.urls')),
    url(r'^api/v1/transactions/', include('transactions.urls.urls_transaction'), name='transactions'),
    url(r'^api/v1/incomes/', include('transactions.urls.urls_transaction_kind'), kwargs={'kind': Transaction.INCOME_KIND}, name='incomes'),
    url(r'^api/v1/expenses/', include('transactions.urls.urls_transaction_kind'), kwargs={'kind': Transaction.EXPENSE_KIND}, name='expenses'),
    url(r'^api/v1/categories/', include('transactions.urls.urls_category')),
]