from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_expiring_authtoken.models import ExpiringToken
from auth.serializers import LoginSerializer

class AuthView(APIView):
    permission_classes = []

    def post(self, request, format='json'):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email, pwd = serializer.data.values()

        try:
            user = User.objects.get(email=email)
            
            if user.check_password(pwd):
                token = self.get_token(user)
                return Response({'token': token.key}, status.HTTP_200_OK)

        except User.DoesNotExist:
            pass

        raise AuthenticationFailed()

    def get_token(self, user):
        try:
            token = ExpiringToken.objects.get(user=user)

            if token.expired():
                token.delete()
                token = ExpiringToken.objects.create(user=user)

        except ExpiringToken.DoesNotExist:
            token = ExpiringToken.objects.create(user=user)

        return token