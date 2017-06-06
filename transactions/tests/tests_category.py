from unittest import skip
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from transactions.models import Category
from transactions.tests.base_test import BaseTestHelper

class CategoryTestCase(APITestCase, BaseTestHelper):

    def setUp(self):
        self.user, token = self.create_user('testuser', email='testuser@test.com', password='testing')

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        self.account = self.create_account(self.user)

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

        url = reverse('expense-category', kwargs={'pk':category_dto['id']})
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

    def test_list_only_user_categories(self):
        self.create_category('eating')
        self.create_category('market')
        self.create_category('travel')
        self.create_category('car')

        other_user = self.create_user('other', email='other_user@email.com', password='123456')[0]
        self.create_category('', user=other_user)

        response = self.client.get(reverse('expense-categories'), format='json')
        self.assertEqual(len(response.data), 4)

    def test_cant_delete_category_in_use(self):
        category = self.create_category('in_use')
        self.create_transaction(category=category)

        url = reverse('expense-category', kwargs={'pk':category.id})
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Category.objects.count(), 1)

    def test_can_delete_category_not_in_use(self):
        category = self.create_category('eating')

        url = reverse('expense-category', kwargs={'pk':category.id})
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Category.objects.count(), 0)

    def test_get_categories_by_kind(self):
        self.create_category('eating', kind=Category.EXPENSE_KIND)
        self.create_category('salary', kind=Category.INCOME_KIND)
        self.create_category('freelance', kind=Category.INCOME_KIND)

        response = self.client.get(reverse('expense-categories'), format='json')
        self.assertEqual(len(response.data), 1)

        response = self.client.get(reverse('income-categories'), format='json')
        self.assertEqual(len(response.data), 2)

    def test_user_cant_handle_category_it_doesnt_own(self):
        '''
        User should get 404 because it can't access nor handle 
        categories that belongs to other user.
        '''
        other_user, other_token = self.create_user('other_user', email='other_user@hotmail.com', password='pass')
        category_from_other_user = self.create_category('other users category', other_user)        
        
        category_dto = {'name': 'new name'}

        url = reverse('expense-category', kwargs={'pk':category_from_other_user.id})
        
        response = self.client.put(url, category_dto, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)