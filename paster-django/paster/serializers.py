import os
from collections import OrderedDict

from django.core.validators import ProhibitNullCharactersValidator
from django.db.models import fields
from django.utils.functional import empty
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from rest_framework.fields import FileField, SkipField, ImageField
from rest_framework.relations import PKOnlyObject

from .models import *

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
