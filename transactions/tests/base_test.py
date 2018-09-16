import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import signals
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from transactions import signals as transactions_signals
from transactions.models import Account, Category, HasKind, Transaction
from users import signals as user_signals


class BaseTestHelperFactory:
    """
    Created to be used on setupTestData and be faster. When possible old BaseTestHelper will be extinguished.
    """

    @classmethod
    def create_transaction(cls, value=None, description='description', kind=None, account=None, category=None,
                           due_date=datetime.datetime.today(), payment_date=None, priority=1, deadline=10):
        if value is None:
            value = cls.value

        if account is None:
            account = cls.account

        if category is None:
            category = cls.category

        if kind is None:
            kind = Transaction.EXPENSE_KIND if value <= 0 else Transaction.INCOME_KIND

        transaction = Transaction.objects.create(
            account=account,
            due_date=due_date,
            description=description,
            category=category,
            value=value,
            kind=kind,
            payment_date=payment_date,
            priority=priority,
            deadline=deadline
        )

        return transaction

    @classmethod
    def create_account(cls, user=None, name='default', current_effective_balance=0, current_real_balance=0, **kwargs):
        if user is None:
            user = cls.user

        return Account.objects.create(name=name, user=user,
            current_effective_balance=current_effective_balance,
            current_real_balance=current_real_balance, **kwargs)

    @classmethod
    def create_user(cls, name='testuser', **kwargs):
        user = User.objects.create_user(kwargs)
        token = Token.objects.get(user=user)

        return user, token

    @classmethod
    def create_category(cls, name, user=None, kind=Category.EXPENSE_KIND):
        if user is None:
            user = cls.user

        return Category.objects.create(kind=kind, user=user, name=name)

    @classmethod
    def create_authenticated_client(cls, token):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        return client


class UserDataTestSetupMixin(BaseTestHelperFactory):
    @classmethod
    def setUpTestData(cls):
        cls.user, cls.token = cls.create_user('testuser', email='testuser@test.com', password='testing')
        cls.account = cls.create_account()
        cls.expense_category = cls.create_category('cat_exp', kind=HasKind.EXPENSE_KIND)
        cls.income_category = cls.create_category('cat_inc', kind=HasKind.INCOME_KIND)
        cls.category = cls.expense_category  # default
        super().setUpTestData()


class OtherUserDataTestSetupMixin(BaseTestHelperFactory):
    @classmethod
    def setUpTestData(cls):
        other_user, other_token = cls.create_user('other', email='other@test.com', password='pass')
        other_account = cls.create_account(user=other_user)
        other_category = cls.create_category('category', user=other_user)
        cls.other_user = other_user
        cls.other_user_token = other_token
        cls.other_user_data = {
            'account': other_account,
            'category': other_category
        }
        super().setUpTestData()


class WithoutSignalsMixin:
    TRANSACTION_PERIODICS = {"func": transactions_signals.updates_periodics_parent, "sender": Transaction}
    ACCOUNT_START_BALANCE = {"func": transactions_signals.creates_start_balance, "sender": Account}
    USERS_ACCOUNT = {"func": user_signals.create_account, "sender": settings.AUTH_USER_MODEL}

    disabled = [TRANSACTION_PERIODICS, ACCOUNT_START_BALANCE, USERS_ACCOUNT]
    signals_except = []

    @classmethod
    def setUpTestData(cls):
        for signal in cls.disabled:
            if signal not in cls.signals_except:
                signals.post_save.disconnect(
                    signal['func'],
                    sender=signal['sender']
                )

        super().setUpTestData()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

        for signal in cls.disabled:
            signals.post_save.connect(
                signal['func'],
                sender=signal['sender']
            )


class BaseTestHelper:
    '''
    Class used to create some resources to backup tests
    '''

    def create_transaction(self, value=None, description='description', kind=None, account=None, category=None,
                           due_date=datetime.datetime.today(), payment_date=None, priority=0, deadline=10):
        if value is None:
            value = self.value

        if account is None:
            account = self.account

        if category is None:
            category = self.category

        if kind is None:
            kind = Transaction.EXPENSE_KIND if value <= 0 else Transaction.INCOME_KIND

        transaction = Transaction.objects.create(
            account=account,
            due_date=due_date,
            description=description,
            category=category,
            value=value,
            kind=kind,
            payment_date=payment_date,
            priority=priority,
            deadline=deadline
            )

        return transaction

    def create_account(self, user=None, name='default', current_effective_balance=0, current_real_balance=0):
        if user is None:
            user = self.user

        return Account.objects.create(name=name, user=user,
            current_effective_balance=current_effective_balance,
            current_real_balance=current_real_balance)

    def create_user(self, name='testuser', **kwargs):
        user = User.objects.create_user(kwargs)
        token = Token.objects.get(user=user)

        return user, token

    def create_category(self, name, user=None, kind=Category.EXPENSE_KIND):
        if user is None:
            user = self.user

        return Category.objects.create(kind=kind, user=user, name=name)

    def create_authenticated_client(self, token):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        return client
