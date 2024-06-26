from random import randint
import re
from urllib import response
from django.db.models.deletion import SET_NULL
from django.shortcuts import render
from rest_framework import status, generics, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.password_validation import validate_password
from django.core.paginator import Paginator

from paster.models import ConfirmCode, User
from paster.serializers import *
from paster.tasks import *

import paster.utils

import os
import json
from datetime import date


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
        params = request.GET

        if 'vk_id' in params.keys():
            vk_id = params['vk_id']
            try:
                member = Member.objects.get(vk_id=vk_id)
            except Member.DoesNotExist:
                member_serializer = MemberSerializer(data=params)
                member_serializer.is_valid(raise_exception=True)
                member = member_serializer.save()
        else:
            raise ValidationError({'info': 'vk_id expected'})

        if random.random() > 0.95:
            paster.utils.accumulate()
        pastes = Paste.objects.all()
        cnt = len(pastes)
        rand_id = random.randint(0, cnt-1)
        return Response(self.serializer_class(instance=pastes[rand_id], context={'member': member}).data, status=status.HTTP_200_OK)


    @action(methods=['GET'], detail=False, url_path='get/unrelated', url_name='Get most unrelated paste', permission_classes=permission_classes)
    def get_unrelated(self, request, *args, **kwargs):
        params = request.GET
        if random.random() > 0.95:
            paster.utils.accumulate()

        if 'vk_id' in params.keys():
            vk_id = params['vk_id']
            try:
                member = Member.objects.get(vk_id=vk_id)
            except Member.DoesNotExist:
                member_serializer = MemberSerializer(data=params)
                member_serializer.is_valid(raise_exception=True)
                member = member_serializer.save()

            related = [x.paste.id for x in Mark.objects.filter(member=member)]
            pastes = sorted(Paste.objects.all().exclude(id__in=related), key=lambda t: t.cnt)

            if pastes:
                # min_cnt = pastes[0].cnt
                # pastes = [x for x in pastes if x.cnt == min_cnt]
                return Response(self.serializer_class(instance=pastes[random.randint(0, len(pastes)-1)], context={'member': member}).data, status=status.HTTP_200_OK)
            else:
                paste = paster.utils.accumulate()
                return Response(self.serializer_class(instance=paste, context={'member': member}).data, status=status.HTTP_200_OK)
        else:
            pastes = sorted(Paste.objects.all(), key=lambda t: t.cnt)
            flag = True
            tmp_cnt = pastes[0].cnt
            for paste in pastes[1:]:
                if paste.cnt != tmp_cnt:
                    flag = False
            if flag and tmp_cnt != 0:
                paste = paster.utils.accumulate()
                return Response(self.serializer_class(instance=paste).data, status=status.HTTP_200_OK)
            else:
                min_cnt = pastes[0].cnt
                pastes = [x for x in pastes if x.cnt == min_cnt]
                return Response(self.serializer_class(instance=pastes[random.randint(0, len(pastes)-1)]).data, status=status.HTTP_200_OK)

    
    @action(methods=['GET'], detail=False, url_path='get/untaged', url_name='Get untaged paste', permission_classes=permission_classes)
    def get_untaged(self, request, *args, **kwargs):
        params = request.GET

        if 'vk_id' in params.keys():
            vk_id = params['vk_id']
            try:
                member = Member.objects.get(vk_id=vk_id)
            except Member.DoesNotExist:
                member_serializer = MemberSerializer(data=params)
                member_serializer.is_valid(raise_exception=True)
                member = member_serializer.save()
            if not member.is_moder:
                return Response({'info': 'You are not allowed'}, status=status.HTTP_403_FORBIDDEN)

            pastes = Paste.objects.filter(tags=None)
            if pastes:
                paste = pastes[random.randint(0, len(pastes)-1)]
            else:
                paste = paster.utils.accumulate()
            res = self.serializer_class(instance=paste, context={'member': member}).data
            tagged = Paste.objects.filter(~Q(tags=None))
            unposted = Paste.objects.filter(Q(last_publicate=None))
            res['untaged'] = len(pastes)
            res['tagged'] = len(tagged)
            res['unposted'] = len(unposted)
            return Response(res, status=status.HTTP_200_OK)
        else:
            return Response({'info': 'You are not allowed'}, status=status.HTTP_403_FORBIDDEN)

    @action(methods=['GET'], detail=False, url_path='all/rating', url_name='Get all pastes to rating', permission_classes=permission_classes)
    def get_all_rating(self, request, *args, **kwargs):
        params = request.GET

        pastes = Paste.objects.all()
        return Response(PasteRatingSerializer(instance=pastes, many=True).data, status=status.HTTP_200_OK)

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

    @action(methods=['POST'], detail=False, url_path='tag', url_name='Tag paste', permission_classes=permission_classes)
    def tag(self, request, *args, **kwargs):
        data = request.data
        paste = Paste.objects.get(id=data.get('id'))
        serializer = self.serializer_class(data=data, instance=paste)
        serializer.is_valid(raise_exception=True)
        if serializer.tag(instance=paste, validated_data=data):
            return Response({'status': 'ok'})
        else:
            return Response({'status': 'error'})


    @action(methods=['POST'], detail=False, url_path='add', url_name='Add paste to base', permission_classes=permission_classes)
    def add_paste(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        paste = serializer.save()
        return Response(self.serializer_class(instance=paste).data)

    @action(methods=['GET'], detail=False, url_path='get/all', url_name='Get all pastes', permission_classes=permission_classes)
    def get_all(self, request, *args, **kwargs):
        params = request.GET
        tag = params.get('tag', None)
        cnt = params.get('cnt', 20)
        page = params.get('page', 1)
        if tag:
            pastes = Paste.objects.filter(tags=tag).distinct()
        else:
            pastes = Paste.objects.all()
        p = Paginator(pastes, cnt)
        try:
            page_ = p.page(page)
        except Exception:
            return Response({'info': 'Page not found'}, status=status.HTTP_404_NOT_FOUND)
        pastes = page_.object_list
        res = {'response': PasteListSerializer(instance=pastes, many=True).data}
        res['page_cnt'] = p.num_pages
        return Response(res, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='get/top', url_name='Get top pastes', permission_classes=permission_classes)
    def get_top(self, request, *args, **kwargs):
        pastes = sorted(Paste.objects.all(), key=lambda t: t.rating, reverse=True)[:20]
        return Response(PasteListSerializer(instance=pastes, many=True).data, status=status.HTTP_200_OK)

    @action(methods=['DELETE'], detail=False, url_path='delete', url_name='Delete paste', permission_classes=permission_classes)
    def delete_paste(self, request, *args, **kwargs):
        data = request.data
        paste = Paste.objects.get(id=data.get('id'))
        serializer = self.serializer_class(data=data, instance=paste)
        serializer.is_valid(raise_exception=True)
        if serializer.delete(instance=paste, validated_data=data):
            return Response({'status': 'ok'})
        else:
            return Response({'status': 'already'})

    @action(methods=['POST'], detail=False, url_path='accumulate', url_name='Accumulate pastes', permission_classes=permission_classes)
    def accumulate(self, request, *args, **kwargs):
        data = request.data
        sources = data.get("sources", [])
        count = data.get("count", 10)
        if sources:
            sources_objects = Source.objects.filter(id__in=sources)
        else:
            sources_objects = Source.objects.all()
        for _ in range(count):
            paster.utils.accumulate(sources=sources_objects)
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class PasteTagView(viewsets.ViewSet):
    """
    Работа с тегами пастами
    """
    permission_classes = (AllowAny, )
    serializer_class = PasteTagSerializer

    @action(methods=['GET'], detail=False, url_path='all', url_name='Get all paste tags', permission_classes=permission_classes)
    def get_paste_tags(self, request, *args, **kwargs):
        tags = PasteTag.objects.all()
        return Response(self.serializer_class(instance=tags, many=True).data, status=status.HTTP_200_OK)


class MemberView(viewsets.ViewSet):
    """
    Работа с участниками
    """
    permission_classes = (AllowAny, )
    serializer_class = MemberSerializer

    @action(methods=['GET'], detail=False, url_path='get/(?P<id>\d+)', url_name='Get member', permission_classes=permission_classes)
    def get_member(self, request, id, *args, **kwargs):
        member = Member.objects.get(id=id)
        return Response(self.serializer_class(instance=member).data, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='get_vk/(?P<id>\d+)', url_name='Get member by vk', permission_classes=permission_classes)
    def get_vk_member(self, request, id, *args, **kwargs):
        member = Member.objects.get(vk_id=id)
        return Response(self.serializer_class(instance=member).data, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='get/top', url_name='Get top members', permission_classes=permission_classes)
    def get_top_members(self, request, *args, **kwargs):
        members = sorted(Member.objects.all(), key=lambda t: t.cnt, reverse=True)[:20]
        return Response(MemberListSerializer(instance=members, many=True).data, status=status.HTTP_200_OK)


class WallView(viewsets.ViewSet):
    """
    Работа со стеной
    """
    permission_classes = (AllowAny, )
    serializer_class = MemberSerializer

    @action(methods=['GET'], detail=False, url_path='test', url_name='Test wall', permission_classes=permission_classes)
    def test_wall(self, request, *args, **kwargs):
        # daily_post.delay()
        regular_post.delay()
        return Response(status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='suggests', url_name='Get all suggests', permission_classes=permission_classes)
    def get_suggests_view(self, request, *args, **kwargs):
        # res = paster.utils.get_suggests()
        pastes = PasteSuggest.objects.all()
        count = pastes.count()
        if count == 0:
            res = {'count': count}
        else:
            paste = pastes.first()
            res = {'count': count, 'item': {"id": paste.id, "text": paste.text}, 'member': {'id': paste.sender, 'name': paste.sender_nickname}}
        return Response(res, status=status.HTTP_200_OK)
    
    @action(methods=['POST'], detail=False, url_path='suggests/add', url_name='Add new suggest', permission_classes=permission_classes)
    def add_suggests_view(self, request, *args, **kwargs):
        data = request.data
        serializer = PasteSuggestSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        paste = serializer.save()
        return Response(PasteSuggestSerializer(instance=paste).data)

    @action(methods=['POST'], detail=False, url_path='suggests/post', url_name='Post suggest', permission_classes=permission_classes)
    def post_suggest_view(self, request, *args, **kwargs):
        data = request.data
        suggest = PasteSuggest.objects.get(id=data['id'])
        paste = Paste.objects.create(text=suggest.text, link=''.join(random.choices('qwertyuiopasdfghjklzxcvbnm1234567890', k=10)))
        for tag in data['tags']:
            paste.tags.add(tag)
        paste.save()
        suggest.delete()

        # res = paster.utils.post_suggest(data['id'], data['tags'])
        return Response({"status": "ok"}, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False, url_path='suggests/deny', url_name='Deny suggest', permission_classes=permission_classes)
    def deny_suggest_view(self, request, *args, **kwargs):
        data = request.data
        PasteSuggest.objects.get(id=data['id']).delete()
        # res = paster.utils.deny_suggest(data['id'])
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class ChatView(viewsets.ViewSet):
    """
    Работа с чатами
    """
    permission_classes = (AllowAny, )
    serializer_class = ChatSerializer

    @action(methods=['POST'], detail=False, url_path='create', url_name='Create chat', permission_classes=permission_classes)
    def create_chat(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        chat = serializer.save()
        return Response(self.serializer_class(instance=chat).data, status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=False, url_path='update', url_name='Update chat', permission_classes=permission_classes)
    def update_chat(self, request, *args, **kwargs):
        data = request.data
        
        chat = Chat.objects.get(chat_id=data.get('chat_id'))
        if "enable" in data.keys():
            chat.messages_enabled = data['enable']
        chat.save()
        return Response(self.serializer_class(instance=chat).data, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='refresh', url_name='Refresh chat names', permission_classes=permission_classes)
    def refresh_chats(self, request, *args, **kwargs):
        chats = Chat.objects.all()
        for chat in chats:
            chat.name = paster.utils.get_chat_name(chat.chat_id)
            chat.save()
        return Response({'info': 'ok'}, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='get/(?P<id>\d+)', url_name='Get chat', permission_classes=permission_classes)
    def get_chat(self, request, id, *args, **kwargs):
        chat, created = Chat.objects.get_or_create(chat_id=id)
        if created:
            chat.save()
        return Response(self.serializer_class(instance=chat).data, status=status.HTTP_200_OK)

    
class SourceView(viewsets.ViewSet):
    """
    Работа с источниками
    """
    permission_classes = (AllowAny, )
    serializer_class = SourceSerializer

    @action(methods=['GET'], detail=False, url_path='get', url_name='Get sources', permission_classes=permission_classes)
    def get_sources(self, request, *args, **kwargs):
        sources = Source.objects.all()
        return Response(self.serializer_class(instance=sources, many=True).data, status=status.HTTP_200_OK)
