from datetime import date
from unittest import mock, skip
from django.test import TestCase
from transactions.serializers.PeriodicSerializer import PeriodicSerializer
from common.tests_helpers import SerializerTestHelper

class PeriodicSerializerTestCase(TestCase, SerializerTestHelper):
    def setUp(self):
        self.serializer_data = {
            'frequency': 'daily',
            'interval': 1,
        }

    def test_serializer_validates_with_how_many(self):
        data = self.get_data(how_many=2)
        serializer = PeriodicSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_serializer_validates_with_until(self):
        data = self.get_data(until=date(2018, 3, 20))
        serializer = PeriodicSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_serializer_how_many_should_not_allows_below_zero(self):
        data = self.get_data(how_many=0)
        serializer = PeriodicSerializer(data=data)
        self.assert_has_field_error(serializer, 'how_many')

    def test_serializer_should_not_allow_both_until_with_how_many(self):
        data = self.get_data(how_many=2, until=date(2018, 3, 20))
        serializer = PeriodicSerializer(data=data)
        self.assert_has_field_error(serializer)

    def test_serializer_should_not_allow_missing_both_until_with_how_many(self):
        serializer = PeriodicSerializer(data=self.serializer_data)
        self.assert_has_field_error(serializer)
