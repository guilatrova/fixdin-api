from django.conf.urls import url

from users import views

list_users = views.UserViewSet.as_view({'post': 'create'})

urlpatterns = [
    url(r'^$', views.AuthAPIView.as_view(), name='login'),
    url(r'^users/$', list_users, name='users'),
]
