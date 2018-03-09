from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from paymentorders.services import NextExpensesService

class PaymentOrderAPIView(APIView):
    def get(self, request):
        service = NextExpensesService(self.request.user.id, )

