from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from transactions.models import Category

class CategoryTestCase(APITestCase):

    def setUp(self):
        self.user, token = self.create_user('testuser', email='testuser@test.com', password='testing')

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
        self.create_category('eating')

        category_dto = {
            'name': 'eating'
        }

        response = self.client.post(reverse('expense-categories'), category_dto, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Category.objects.count(), 1)

    def test_cant_create_category_repeated_name_regardless_character_casing(self):
        self.create_category('eating')

        category_dto = {
            'name': 'Eating'
        }

        response = self.client.post(reverse('expense-categories'), category_dto, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Category.objects.count(), 1)

    def test_cant_rename_category_same_other_name(self):
        self.create_category('eating')
        category = self.create_category('car')

        category_dto = {
            'id': category.id,
            'name': 'eating' #changed name
        }

        url = reverse('retrieve-expense-categories', kwargs={'pk':category_dto['id']})
        response = self.client.put(url, category_dto, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Category.objects.count(), 2)

    def test_different_users_can_create_categories_with_same_name(self):
        other_user, other_token = self.create_user('other_user', email='other_user@hotmail.com', password='pass')

        other_client = APIClient()
        other_client.credentials(HTTP_AUTHORIZATION='Token ' + other_token.key)

        category_dto = {'name': 'eating'}

        response = self.client.post(reverse('expense-categories'), category_dto, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = other_client.post(reverse('expense-categories'), category_dto, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_user_categories(self):
        self.create_category('eating')
        self.create_category('market')
        self.create_category('travel')
        self.create_category('car')

        other_user = self.create_user('other', email='other_user@email.com', password='123456')[0]
        self.create_category('', user=other_user)

        response = self.client.get(reverse('expense-categories'), format='json')
        self.assertEqual(len(response.data), 4) #ignore others categories


    def create_user(self, name='testuser', **kwargs):
        user = User.objects.create_user(kwargs)
        user.save()
        token = Token.objects.create(user=user)
        token.save()

        return user, token

    def create_category(self, name, user=None):
        if user is None:
            user = self.user

        category = Category.objects.create(kind=Category.EXPENSE_KIND, user=user, name=name)
        category.save()
        return category