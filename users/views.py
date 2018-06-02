from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import render
from rest_framework import status, views, viewsets
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_expiring_authtoken.models import ExpiringToken

from users.serializers import LoginSerializer, UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer

    def get_queryset(self):
        return settings.AUTH_USER_MODEL.objects()

    def get_permissions(self):
        if self.request.method == 'POST':
            self.permission_classes = (AllowAny,)

        return super(UserViewSet, self).get_permissions()

class AuthAPIView(views.APIView):
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
