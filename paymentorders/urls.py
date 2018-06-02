from django.conf.urls import url

from paymentorders import views

urlpatterns = [
    url(r'^$', views.PaymentOrderAPIView.as_view(), name="payment-orders"),
]
