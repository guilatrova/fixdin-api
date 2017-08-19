from django.conf.urls import url
from reports import views

urlpatterns = [
    url(r'^expenses/$', views.Last13MonthsAPIView.as_view(), name="last-13-months"),
]