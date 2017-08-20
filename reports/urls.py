from django.conf.urls import url
from reports import views

urlpatterns = [
    url(r'^last-13-months/$', views.Last13MonthsAPIView.as_view(), name="last-13-months"),
    url(r'^next-expenses/$', views.NextExpensesAPIView.as_view(), name="next-expenses")
]