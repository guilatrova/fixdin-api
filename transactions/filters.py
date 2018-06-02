from datetime import datetime

from transactions.models import HasKind


class TransactionFilter:
    def get_query_params_filter(self):
        dic = {}
        
        description = self.request.query_params.get('description', False)
        if description:
            dic['description__icontains'] = description

        categories = self.request.query_params.get('category', False)
        if categories:
            dic['category_id__in'] = categories.split(',')

        accounts = self.request.query_params.get('account', False)
        if accounts:
            dic['account_id__in'] = accounts.split(',')

        priority = self.request.query_params.get('priority', False)
        if priority:
            dic['priority'] = priority

        deadline = self.request.query_params.get('deadline', False)
        if deadline:
            dic['deadline'] = deadline

        kind = self.request.query_params.get('kind', False)
        if kind in [str(HasKind.EXPENSE_KIND), str(HasKind.INCOME_KIND)]:
            dic['kind'] = kind

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
            today = datetime.today()
            dic['due_date__month'] = today.month
            dic['due_date__year'] = today.year

        return dic
