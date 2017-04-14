from rest_framework import serializers

class LoginSerializer(serializers.Serializer):
    user = serializers.CharField(max_length=40)
    password = serializers.CharField(max_length=40)
