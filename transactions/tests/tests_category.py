from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from common.tests_helpers import SerializerTestHelper
from transactions.models import Category
from transactions.serializers import CategorySerializer
from transactions.tests.base_test import (BaseTestHelper, OtherUserDataTestSetupMixin, UserDataTestSetupMixin,
                                          WithoutSignalsMixin)


class CategoryApiTestCase(WithoutSignalsMixin, APITestCase, BaseTestHelper):

    def setUp(self):
        self.user, token = self.create_user('testuser', email='testuser@test.com', password='testing')

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        self.account = self.create_account(self.user)
        self.value = 1

    def test_create_category(self):
        category_dto = {
            'name': 'eating',
            'kind': Category.INCOME_KIND
        }

        response = self.client.post(reverse('categories'), category_dto, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 1)

    def test_cant_create_category_repeated_name_regardless_character_casing(self):
        self.create_category('eating')

        category_dto = {
            'name': 'Eating'
        }

        response = self.client.post(reverse('categories'), category_dto, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Category.objects.count(), 1)

    def test_cant_rename_category_same_other_name(self):
        self.create_category('eating')
        category = self.create_category('car')

        category_dto = {
            'id': category.id,
            'name': 'eating'  # changed name
        }

        url = reverse('category', kwargs={'pk': category_dto['id']})
        response = self.client.put(url, category_dto, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Category.objects.count(), 2)

    def test_list_only_user_categories(self):
        self.create_category('eating')
        self.create_category('market')
        self.create_category('travel')
        self.create_category('car')

        other_user = self.create_user('other', email='other_user@email.com', password='123456')[0]
        self.create_category('', user=other_user)

        response = self.client.get(reverse('categories'), format='json')
        self.assertEqual(len(response.data), 4)

    def test_cant_delete_category_in_use(self):
        category = self.create_category('in_use')
        self.create_transaction(category=category)

        url = reverse('category', kwargs={'pk': category.id})
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Category.objects.count(), 1)

    def test_can_delete_category_not_in_use(self):
        category = self.create_category('eating')

        url = reverse('category', kwargs={'pk': category.id})
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Category.objects.count(), 0)

    def test_user_cant_handle_category_it_doesnt_own(self):
        '''
        User should get 404 because it can't access nor handle
        categories that belongs to other user.
        '''
        other_user, other_token = self.create_user('other_user', email='other_user@hotmail.com', password='pass')
        category_from_other_user = self.create_category('other users category', other_user)

        category_dto = {'name': 'new name'}

        url = reverse('category', kwargs={'pk': category_from_other_user.id})

        response = self.client.put(url, category_dto, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_api_changes_kinds_updates_transactions(self):
        category = self.create_category('kind_changer', kind=Category.EXPENSE_KIND)
        transaction = self.create_transaction(-100, category=category)
        change_to = Category.INCOME_KIND

        category_dto = {'name': 'kind_changer', 'kind': change_to}

        url = reverse('category', kwargs={'pk': category.id})

        response = self.client.put(url, category_dto, format='json')
        transaction.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(transaction.kind, change_to)
        self.assertEqual(transaction.value, 100)


class CategorySerializerTestCase(UserDataTestSetupMixin, OtherUserDataTestSetupMixin, TestCase, SerializerTestHelper):

    def setUp(self):
        self.serializer_data = {
            'name': 'Category',
            'kind': Category.EXPENSE_KIND
        }
        self.context = {
            'user_id': self.user.id
        }

    def test_serializer_validates(self):
        serializer = CategorySerializer(data=self.serializer_data, context=self.context)
        self.assertTrue(serializer.is_valid())

    def test_serializer_should_not_allow_create_same_name(self):
        data = {
            'name': self.category.name,
            'kind': self.category.kind
        }
        serializer = CategorySerializer(data=data, context=self.context)
        self.assert_has_field_error(serializer)

    def test_serializer_allows_same_name_for_different_users(self):
        data = {
            'name': self.category.name,
            'kind': self.category.kind
        }
        context = {
            'user_id': self.other_user.id
        }
        serializer = CategorySerializer(data=data, context=context)
        self.assertTrue(serializer.is_valid())

    def test_block_names_ending_with_sys(self):
        data = self.serializer_data
        data["name"] = "anything_sys"

        serializer = CategorySerializer(data=data, context=self.context)

        self.assert_has_field_error(serializer, "name")
