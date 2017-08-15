from django.shortcuts import render
from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from transactions.models import Category, Transaction, Account

class BalanceAPIView(APIView):

    def get(self, request, format='json'):
        total_sum = Transaction.objects.filter(account__user_id=request.user.id).aggregate(Sum('value'))['value__sum']
        return Response({ 'balance': total_sum })