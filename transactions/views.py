from datetime import datetime
from django.shortcuts import render
from rest_framework import viewsets, status, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from transactions.models import Category, Transaction, Account
from transactions.serializers import CategorySerializer, TransactionSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.filter(kind=self.kwargs['kind'], user_id=self.request.user.id)

    def get_serializer_context(self):
        return {
            "user_id": self.request.user.id,
            "kind": self.kwargs['kind']
        }

    def destroy(self, request, *args, **kwargs):
        if Transaction.objects.filter(category_id=kwargs['pk']).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'detail': 'Some transactions are using this category'})

        return super(CategoryViewSet, self).destroy(self, request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, kind=self.kwargs['kind'])

class TransactionFilter:
    def get_query_params_filter(self):
        dic = {}
        
        description = self.request.query_params.get('description', False)
        if description:
            dic['description__icontains'] = description

        categories = self.request.query_params.get('category', False)
        if categories:
            dic['category_id__in'] = categories.split(',')

        priority = self.request.query_params.get('priority', False)
        if priority:
            dic['priority'] = priority

        deadline = self.request.query_params.get('deadline', False)
        if deadline:
            dic['deadline'] = deadline

        payed = self.request.query_params.get('payed', False)
        has_filter_by_payment_date = False
        if payed and payed != '-1':
            dic['payment_date__isnull'] = (payed == '0')

            payment_date_from = self.request.query_params.get('payment_date_from', False)
            payment_date_until = self.request.query_params.get('payment_date_until', False)
            if payment_date_from and payment_date_until:
                has_filter_by_payment_date = True
                range_from = datetime.strptime(payment_date_from, '%Y-%m-%d')
                range_until = datetime.strptime(payment_date_until, '%Y-%m-%d')

                dic['payment_date__range'] = [range_from, range_until]

        due_date_from = self.request.query_params.get('due_date_from', False)
        due_date_until = self.request.query_params.get('due_date_until', False)
        if due_date_from and due_date_until:
            range_from = datetime.strptime(due_date_from, '%Y-%m-%d')
            range_until = datetime.strptime(due_date_until, '%Y-%m-%d')

            dic['due_date__range'] = [range_from, range_until]
        elif self.request.method == 'GET' and not has_filter_by_payment_date:
            pass #JUST WHILE IN DEV PHASE
            # today = datetime.today()
            # dic['due_date__month'] = today.month
            # dic['due_date__year'] = today.year

        return dic

class TransactionViewSet(viewsets.ModelViewSet, TransactionFilter):
    '''
    Handles /expenses and /incomes endpoints
    '''
    serializer_class = TransactionSerializer

    def get_serializer_context(self):
        return {
            "kind": self.kwargs['kind'],
            "user_id": self.request.user.id
        }

    def get_queryset(self):
        query_filter = { 
            'account__user_id': self.request.user.id,
            'kind': self.kwargs['kind'] 
        }
        
        url_query_params = self.get_query_params_filter()  
        query_filter.update(url_query_params)
        return Transaction.objects.filter(**query_filter)

    def patch_all_periodics(self, request, *args, **kwargs):
        periodic = self.request.query_params.get('periodic_transaction', False)
        if periodic:
            queryset = self.filter_queryset(Transaction.objects.filter(periodic_transaction=periodic))
            data = request.data
            to_return = []

            for instance in queryset:
                serializer = self.get_serializer(instance, data=data, partial=True)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
                to_return.append(serializer.data)

            return Response(to_return)

        return Response(status=status.HTTP_404_NOT_FOUND)

    def destroy_all_periodics(self, request, *args, **kwargs):
        periodic = self.request.query_params.get('periodic_transaction', False)
        if periodic:
            Transaction.objects.filter(periodic_transaction=periodic).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_404_NOT_FOUND)

    def perform_destroy(self, instance):
        params = self.request.query_params

        if params.get('next', False) == '1':
            Transaction.objects.filter(periodic_transaction=instance.periodic_transaction, due_date__gte=instance.due_date).delete()
        else:
            return super(TransactionViewSet, self).perform_destroy(instance)

    def perform_create(self, serializer):
        account = Account.objects.filter(user_id=self.request.user.id).first()
        serializer.save(kind=self.kwargs['kind'],account=account)

class TransactionAPIView(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet, TransactionFilter):
    '''
    Handles only GET to retrieve all transactions
    '''
    serializer_class = TransactionSerializer

    def get_queryset(self):
        query_filter = { 
            'account__user_id': self.request.user.id,
        }
        
        url_query_params = self.get_query_params_filter()  
        query_filter.update(url_query_params)
        return Transaction.objects.filter(**query_filter)