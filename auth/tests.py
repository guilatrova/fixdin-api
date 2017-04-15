from django.test import TestCase
from rest_framework.test import APITestCase
from unittest import mock
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from rest_framework import status
from rest_framework.authtoken.models import Token

import datetime

class AuthTests(TestCase):
    def test_should_deny_expired_tokens(self):
        StudentFactory().create_new_student('116755', '220814', student_name='Guilherme Magalhaes Latrova', email='guilhermelatrova@hotmail.com')
        student = Student.objects.get(register_id='116755')
        payload = {'ra': '116755', 'password': '220814'}
        expected_response = {'code':1001, 'detail':strings.EXPIRED_TOKEN['detail']}
        client = APIClient()

        #Let's generate the first token
        response = self.client.post('/api/v1/students/auth', payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        expired_token = Token.objects.get(user=student.user)
        self.assertEqual(response.data, {'token': expired_token.key})

        #Now we'll adjust its creation time to 14 days ago (which is its expiration time)
        expired_token.created -= datetime.timedelta(days=14)
        expired_token.save()                
        client.credentials(HTTP_AUTHORIZATION='Token ' + expired_token.key)

        response = client.get('/api/v1/subjects/2016-2')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, expected_response)