from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from transactions.models import Category

class CategoryTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user('testuser', email='testuser@test.com', password='testing')
        self.user.save()
        token = Token.objects.create(user=self.user)
        token.save()

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_create_category(self):
        category_dto = {
            'name': 'eating'
        }

        response = self.client.post(reverse('expense-categories'), category_dto, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 1)

    def test_cant_create_category_repeated_name(self):
        category = Category.objects.create(kind=Category.EXPENSE_KIND, user=self.user, name='eating')
        category.save()

        category_dto = {
            'name': 'eating'
        }

        response = self.client.post(reverse('expense-categories'), category_dto, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Category.objects.count(), 1)