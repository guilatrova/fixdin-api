from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from rest_framework import serializers

class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=40)
    password = serializers.CharField(max_length=40)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'email', 'first_name', 'last_name')
        write_only_fields = ('password',)
        read_only_fields = ('id',)

    def create(self, validated_data):
        user = get_user_model().objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)
        return super(UserSerializer, self).update(instance, validated_data)