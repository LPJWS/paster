import os
from collections import OrderedDict
from django import utils

from django.core.validators import ProhibitNullCharactersValidator
from django.db.models import fields
import requests
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from rest_framework.fields import FileField, SkipField, ImageField
from rest_framework.relations import PKOnlyObject

from .models import *
import paster.utils

class BaseImageSerializer(serializers.ModelSerializer):

    def build_image_url(self, field):
        path = f'{"https" if settings.DEBUG is False else "http"}://' \
               f'{os.getenv("HOST_NAME") if settings.DEBUG is False else "0.0.0.0:8000"}{settings.MEDIA_URL}{field}'
        return path


    def to_representation(self, instance):
        ret = OrderedDict()
        fields = self._readable_fields

        for field in fields:
            try:
                attribute = field.get_attribute(instance)
            except SkipField:
                continue

            check_for_none = attribute.pk if isinstance(attribute, PKOnlyObject) else attribute
            if check_for_none is None:
                ret[field.field_name] = None
            else:
                # тут проверка
                if isinstance(field, ImageField) or isinstance(field, FileField):
                    try:
                        ret[field.field_name] = self.build_image_url(attribute)
                    except:
                        ret[field.field_name] = field.to_representation(attribute)
                else:
                    ret[field.field_name] = field.to_representation(attribute)
        return ret


class AuthorizationSerializer(BaseImageSerializer):
    """ Сериализация авторизации """

    token = serializers.CharField(max_length=255, read_only=True)
    username = serializers.CharField(max_length=50)
    name = serializers.CharField(max_length=50, required=False)
    password = serializers.CharField(max_length=50, write_only=True)
    # password = serializers.CharField(max_length=50, validators=(validate_password,), write_only=True)
    photo = serializers.ImageField(required=False, use_url=True)

    def create(self, validated_data):
        is_signup = self.context['signup']
        user, created = User.objects.get_or_create(username=validated_data.get('username'))
        if created:
            if not is_signup:
                user.delete()
                raise serializers.ValidationError({'info': 'Bad username/password'})
            # user.name = validated_data['name'] # Так почему то он сохраняет в виде кортежа из одного элемента
            setattr(user, 'name', validated_data['name']) # А вот так как строку
            user.set_password(validated_data.get('password'))
            user.photo = validated_data.get('photo')
            user.save()
        else:
            if is_signup:
                raise serializers.ValidationError({'info': f'User with phone/email {validated_data.get("username")} already exists'})
            if not user.check_password(validated_data.get('password')):
                raise serializers.ValidationError({'info': 'Bad username/password'})
        return user

    class Meta:
        model = User
        fields = "__all__"


class UserDetailSerializer(BaseImageSerializer):
    """
    Сериализатор для детального отображения пользователя
    """

    class Meta:
        model = User
        fields = ['username', 'name', 'photo']


class UserUpdateSerializer(BaseImageSerializer):
    """
    Сериализатор для обновления пользователя
    """
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name')
        instance.photo = validated_data.get('photo')
        old_pass = validated_data.get('old_password')
        new_pass = validated_data.get('new_password')
        if old_pass is not None and new_pass is not None:
            if instance.check_password(old_pass):
                # try:
                #     validate_password(new_pass)
                # except Exception as e:
                #     raise ValidationError(e)
                instance.set_password(new_pass)
            else:
                raise ValidationError({'info': 'Wrong password'})
        instance.save()
        return instance

    class Meta:
        model = User
        fields = ['username', 'name', 'photo', 'old_password', 'new_password']


class MemberSerializer(BaseImageSerializer):
    """
    Сериализатор для детального отображения пользователя
    """
    avg = serializers.ReadOnlyField()
    cnt = serializers.ReadOnlyField()
    marks = serializers.SerializerMethodField()

    def get_marks(self, object):
        m_marks = Mark.objects.filter(member=object)
        return MarkSerializer(instance=m_marks, many=True, context=self.context).data

    def create(self, validated_data):
        member, created = Member.objects.get_or_create(
            vk_id=validated_data.get('vk_id')
        )
        if created:
            name = paster.utils.get_name_by_id(validated_data.get('vk_id'))
            member.name = name
            member.save()
        return member

    class Meta:
        model = Member
        fields = '__all__'


class MemberListSerializer(BaseImageSerializer):
    """
    Сериализатор для листингового отображения пользователя
    """
    avg = serializers.ReadOnlyField()
    cnt = serializers.ReadOnlyField()

    def create(self, validated_data):
        member, created = Member.objects.get_or_create(
            vk_id=validated_data.get('vk_id')
        )
        if created:
            name = paster.utils.get_name_by_id(validated_data.get('vk_id'))
            member.name = name
            member.save()
        return member

    class Meta:
        model = Member
        fields = '__all__'


class PasteTagSerializer(BaseImageSerializer):
    """
    Сериализатор для тегов паст
    """

    class Meta:
        model = PasteTag
        fields = '__all__'


class PasteSerializer(BaseImageSerializer):
    """
    Сериализатор для детального отображения пользователя
    """
    avg = serializers.ReadOnlyField()
    cnt = serializers.ReadOnlyField()
    rating = serializers.ReadOnlyField()
    anno = serializers.ReadOnlyField()
    clear_text = serializers.ReadOnlyField()
    group = serializers.ReadOnlyField()
    post = serializers.ReadOnlyField()
    vk_id = serializers.IntegerField(write_only=True, required=False)
    mark = serializers.IntegerField(write_only=True, required=False)
    link = serializers.CharField(required=False)
    pic = serializers.SerializerMethodField()
    pic_link = serializers.SerializerMethodField()
    related = serializers.SerializerMethodField()
    sender = MemberListSerializer(read_only=True)
    tags = PasteTagSerializer(many=True, read_only=True)
    tags_new = serializers.ListField(write_only=True, required=False)

    def get_pic(self, object):
        # return paster.utils.get_pic_by_id(object.link)
        return paster.utils.get_rand_pic(object.link)

    def get_pic_link(self, object):
        # return paster.utils.get_pic_link_by_id(object.link)
        return paster.utils.get_rand_pic_link(object.link)

    def get_related(self, object):
        try:
            Mark.objects.get(paste=object, member=self.context.get('member'))
            return True
        except Mark.DoesNotExist:
            return False

    def create(self, validated_data):
        text = paster.utils.get_text_by_id(validated_data.get('link'))
        try:
            paste = Paste.objects.get(link=validated_data.get('link'), text=text)
        except Paste.DoesNotExist:
            try:
                member = Member.objects.get(vk_id=validated_data.get('vk_id'))
            except Member.DoesNotExist:
                member_serializer = MemberSerializer(data=validated_data)
                member_serializer.is_valid(raise_exception=True)
                member = member_serializer.save()
            paste = Paste.objects.create(link=validated_data.get('link'), text=text, sender=member)
            paste.save()
        return paste

    def relate(self, instance, validated_data):
        try:
            member = Member.objects.get(vk_id=validated_data.get('vk_id'))
        except Member.DoesNotExist:
            member_serializer = MemberSerializer(data=validated_data)
            member_serializer.is_valid(raise_exception=True)
            member = member_serializer.save()
        mark, created = Mark.objects.get_or_create(member=member, paste=instance)
        if created:
            mark.mark = validated_data.get('mark')
            mark.save()
            instance.last_relate = datetime.now()
            instance.save()
            return True
        return False

    def tag(self, instance, validated_data):
        try:
            member = Member.objects.get(vk_id=validated_data.get('vk_id'))
        except Member.DoesNotExist:
            member_serializer = MemberSerializer(data=validated_data)
            member_serializer.is_valid(raise_exception=True)
            member = member_serializer.save()
        if not member.is_moder:
            raise ValidationError({"info": "You are not allowed"})
        instance.tags.clear()
        action = ModerTag.objects.create(member=member, paste=instance)
        for tag_ in validated_data.get('tags_new'):
            instance.tags.add(tag_)
            action.tags.add(tag_)
        action.save()
        return True

    def delete(self, instance, validated_data):
        try:
            member = Member.objects.get(vk_id=validated_data.get('vk_id'))
        except Member.DoesNotExist:
            member_serializer = MemberSerializer(data=validated_data)
            member_serializer.is_valid(raise_exception=True)
            member = member_serializer.save()
        if not member.is_moder:
            raise ValidationError({"info": "You are not allowed"})
        instance.delete()
        return True

    class Meta:
        model = Paste
        fields = '__all__'


class PasteListSerializer(BaseImageSerializer):
    avg = serializers.ReadOnlyField()
    cnt = serializers.ReadOnlyField()
    rating = serializers.ReadOnlyField()
    anno = serializers.ReadOnlyField()
    group = serializers.ReadOnlyField()
    post = serializers.ReadOnlyField()
    tags = PasteTagSerializer(many=True, read_only=True)

    class Meta:
        model = Paste
        exclude = ('text',)


class PasteRatingSerializer(BaseImageSerializer):
    """
    Сериализатор для детального отображения паст для рейтинга
    """
    avg = serializers.ReadOnlyField()
    cnt = serializers.ReadOnlyField()
    rating = serializers.ReadOnlyField()
    clear_text = serializers.ReadOnlyField()

    class Meta:
        model = Paste
        fields = ('id', 'clear_text', 'cnt', 'avg', 'rating')


class PasteSuggestSerializer(BaseImageSerializer):
    """
    Сериализатор для детального отображения паст в предложке
    """
    anno = serializers.ReadOnlyField()
    clear_text = serializers.ReadOnlyField()

    def create(self, validated_data):
        paste_suggest = PasteSuggest.objects.create(
            text=validated_data.get('text'), 
            sender=validated_data.get('sender'), 
            sender_nickname=validated_data.get('sender_nickname')
        )
        paste_suggest.save()
        return paste_suggest

    # def delete(self, instance, validated_data):
    #     try:
    #         member = Member.objects.get(vk_id=validated_data.get('vk_id'))
    #     except Member.DoesNotExist:
    #         member_serializer = MemberSerializer(data=validated_data)
    #         member_serializer.is_valid(raise_exception=True)
    #         member = member_serializer.save()
    #     if not member.is_moder:
    #         raise ValidationError({"info": "You are not allowed"})
    #     instance.delete()
    #     return True

    class Meta:
        model = PasteSuggest
        fields = '__all__'


class MarkSerializer(BaseImageSerializer):
    paste = PasteListSerializer()

    class Meta:
        model = Mark
        fields = '__all__'


class ChatSerializer(BaseImageSerializer):
    """
    Сериализатор для чатов
    """
    name = serializers.CharField(required=False)

    def create(self, validated_data):
        chat, created = Chat.objects.get_or_create(
            chat_id=validated_data.get('chat_id')
        )
        if created:
            chat.save()
        return chat

    class Meta:
        model = Chat
        fields = '__all__'


class SourceSerializer(BaseImageSerializer):
    """
    Сериализатор для источников
    """

    class Meta:
        model = Source
        fields = '__all__'
