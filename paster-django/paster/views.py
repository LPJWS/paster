from random import randint
import re
from django.db.models.deletion import SET_NULL
from django.shortcuts import render
from rest_framework import status, generics, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.password_validation import validate_password

from paster.models import ConfirmCode, User
from paster.serializers import *
from paster.tasks import *

import paster.utils

import os
import json


class AuthView(viewsets.ViewSet):
    """
    Авторизация пользователей + генерация токена
    """
    permission_classes = (AllowAny,)
    serializer_class = AuthorizationSerializer

    @action(methods=['POST'], detail=False, url_path='signup', url_name='Sign Up User', permission_classes=permission_classes)
    def signup(self, request):
        data = request.data
        serializer = self.serializer_class(data=data, context={"signup": True, "request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=False, url_path='signin', url_name='Sign In User', permission_classes=permission_classes)
    def signin(self, request):
        data = request.data
        serializer = self.serializer_class(data=data, context={"signup": False, "request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False, url_path='send', url_name='Send reset code', permission_classes=permission_classes)
    def send_reset_code(self, request):
        """
        Создание кода сброса
        """
        username=request.data.get('username')
        try:
            user = User.objects.get(username=username)
        except Exception:
            return Response({"info": f"there is no user with username {username}"}, status=status.HTTP_400_BAD_REQUEST)
        confirm_code, _ = ConfirmCode.objects.get_or_create(user=user)
        confirm_code.save()

        if re.match(r'^\+7[0-9]{10}$', username):
            # is phone
            return Response({"info": f"confirm code is send to your phone {confirm_code.code}"}, status=status.HTTP_200_OK)
        elif re.match(r'^[\w\.-]+@[\w\.-]+(\.[\w]+)+$', username):
            # is email
            message = f'Ваш код для сброса пароля: {confirm_code.code}'
            send_email.delay(message, username, 'paster Сброс пароля')
            return Response({"info": f"confirm code is send to your email {username}"}, status=status.HTTP_200_OK)
        else:
            # error
            return Response({"info": f"invalid username"}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['POST'], detail=False, url_path='reset', url_name='Reset password', permission_classes=permission_classes)
    def reset_password(self, request):
        """
        Сброс пароля пользователя
        """
        username=request.data.get('username')
        user = User.objects.get(username=username)
        confirm_code_data = int(request.data.get('code'))
        confirm_code = ConfirmCode.objects.filter(user=user).first()
        new_pass = request.data.get('password')
        # try:
        #     validate_password(new_pass)
        # except Exception as e:
        #     return Response({"info": e})
        if confirm_code is None:
            return Response({"info": f"Reset code was not send"}, status=status.HTTP_400_BAD_REQUEST)
        if confirm_code_data != confirm_code.code:
            return Response({"info": f"Wrong code"}, status=status.HTTP_400_BAD_REQUEST)
        confirm_code.delete()
        user.set_password(new_pass)
        user.save()
        return Response({"info": f"Password was reset successfully"}, status=status.HTTP_200_OK)


class UserView(viewsets.ViewSet):
    """
    Обновление профиля пользователя. Вывод информации о пользователе
    Использую экшны только для того, чтобы сохранить исходные роутинги
    """
    permission_classes = (IsAuthenticated, )
    serializer_class = UserUpdateSerializer

    @action(methods=['PATCH'], detail=False, url_path='edit', url_name='Edit User', permission_classes=[IsAuthenticated])
    def edit_user(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(instance=request.user, data=data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserDetailSerializer(instance=user, context={"request": request}).data, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='me', url_name='About User', permission_classes=[IsAuthenticated])
    def about_user(self, request, *args, **kwargs):
        return Response(UserDetailSerializer(instance=request.user, context={"request": request}).data, status=status.HTTP_200_OK)


class PasteView(viewsets.ViewSet):
    """
    Работа с пастами
    """
    permission_classes = (AllowAny, )
    serializer_class = PasteSerializer

    @action(methods=['GET'], detail=False, url_path='get/(?P<id>\d+)', url_name='Get paste', permission_classes=permission_classes)
    def get_paste(self, request, id, *args, **kwargs):
        paste = Paste.objects.get(id=id)
        return Response(self.serializer_class(instance=paste).data, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='get/rand', url_name='Get rand paste', permission_classes=permission_classes)
    def get_rand(self, request, *args, **kwargs):
        if random.random() > 0.7:
            paster.utils.accumulate()
        pastes = Paste.objects.all()
        cnt = len(pastes)
        rand_id = random.randint(0, cnt-1)
        return Response(self.serializer_class(instance=pastes[rand_id]).data, status=status.HTTP_200_OK)


    @action(methods=['GET'], detail=False, url_path='get/unrelated', url_name='Get most unrelated paste', permission_classes=permission_classes)
    def get_unrelated(self, request, *args, **kwargs):
        pastes = sorted(Paste.objects.all(), key=lambda t: t.cnt)

        flag = True
        tmp_cnt = pastes[0].cnt
        for paste in pastes[1:]:
            if paste.cnt != tmp_cnt:
                flag = False
        if flag and tmp_cnt != 0:
            paster.utils.accumulate()
            pastes = sorted(Paste.objects.all(), key=lambda t: t.cnt)
            return Response(self.serializer_class(instance=pastes[0]).data, status=status.HTTP_200_OK)
        else:
            min_cnt = pastes[0].cnt
            pastes = [x for x in pastes if x.cnt == min_cnt]
            return Response(self.serializer_class(instance=pastes[random.randint(0, len(pastes)-1)]).data, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False, url_path='relate', url_name='Relate paste', permission_classes=permission_classes)
    def relate(self, request, *args, **kwargs):
        data = request.data
        paste = Paste.objects.get(id=data.get('id'))
        serializer = self.serializer_class(data=data, instance=paste)
        serializer.is_valid(raise_exception=True)
        if serializer.relate(instance=paste, validated_data=data):
            return Response({'status': 'ok'})
        else:
            return Response({'status': 'already'})

    @action(methods=['POST'], detail=False, url_path='add', url_name='Add paste to base', permission_classes=permission_classes)
    def add_paste(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        paste = serializer.save()
        return Response(self.serializer_class(instance=paste).data)


    @action(methods=['GET'], detail=False, url_path='get/top', url_name='Get top pastes', permission_classes=permission_classes)
    def get_top(self, request, *args, **kwargs):
        pastes = sorted(Paste.objects.all(), key=lambda t: t.avg, reverse=True)
        return Response(self.serializer_class(instance=pastes, many=True).data, status=status.HTTP_200_OK)
