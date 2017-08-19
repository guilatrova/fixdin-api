from django.conf.urls import url
from reports import views

urlpatterns = [
    url(r'^last-13-months/$', views.Last13MonthsAPIView.as_view(), name="last-13-months"),
]