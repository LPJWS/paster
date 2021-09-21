from datetime import datetime, timedelta
from django.utils import timezone
from email.policy import default
import random
from typing import List
from django.db.models.deletion import CASCADE, SET_NULL
import jwt as jwt
from django.contrib.auth.models import AbstractUser
from django.db import models
from configs import settings

from .validators import *


class User(AbstractUser):
    """
    [User]
    Переопределенный класс пользователя. Использует кастомный менеджер.
    """

    name = models.CharField(max_length=30, blank=True, null=True, verbose_name="имя пользователя")
    username = models.CharField(max_length=50, unique=True, verbose_name='номер телефона/email')
    photo = models.ImageField(upload_to='user_images', blank=True, null=True)

    USERNAME_FIELD = 'username'

    def __str__(self) -> str:
        return f"{self.username}"

    @property
    def token(self) -> str:
        return self._generate_jwt_token()

    def _generate_jwt_token(self) -> str:
        """
        Генерирует веб-токен JSON, в котором хранится идентификатор этого
        пользователя, срок действия токена составляет 30 дней от создания
        """
        dt = datetime.now() + timedelta(days=30)

        token = jwt.encode({
            'id': self.pk,
            'expire': str(dt)
        }, settings.SECRET_KEY, algorithm='HS256')

        return token.decode('utf-8')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class ConfirmCode(models.Model):
    """
    [ConfirmCode]
    Модель кода подтверждения для регистрации
    """
    user = models.ForeignKey(User, on_delete=CASCADE)
    code = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        self.code = random.randint(1000, 9999)
        super(ConfirmCode, self).save(*args, **{})


class Member(models.Model):
    """
    [Member]
    Модель участника проекта
    """
    vk_id = models.IntegerField(unique=True, verbose_name='VK id')

    def __str__(self) -> str:
        return f"{self.vk_id}"

    class Meta:
        verbose_name = 'Участник'
        verbose_name_plural = 'Участники'


class Paste(models.Model):
    """
    [Paste]
    Модель пасты
    """
    link = models.CharField(max_length=150, null=True, blank=True, verbose_name='Ссылка на пасту')
    text = models.TextField(null=True, blank=True, verbose_name='Текст пасты')

    @property
    def avg(self) -> float:
        marks = Mark.objects.filter(paste=self)
        marks_list = [mark.mark for mark in marks]
        if len(marks_list):
            return sum(marks_list)/len(marks_list)
        else:
            return 0

    @property
    def cnt(self) -> int:
        marks = Mark.objects.filter(paste=self)
        return len(marks)

    def __str__(self) -> str:
        return f"{self.link}"

    class Meta:
        verbose_name = 'Паста'
        verbose_name_plural = 'Пасты'


class Mark(models.Model):
    """
    [Mark]
    Модель оценки пасты
    """
    member = models.ForeignKey(Member, null=True, blank=True, on_delete=SET_NULL)
    paste = models.ForeignKey(Paste, on_delete=CASCADE)
    mark = models.IntegerField(default=5, verbose_name='Оценка')

    def __str__(self) -> str:
        return f"{self.member.vk_id} ({self.paste.link}) (self.mark)"

    class Meta:
        verbose_name = 'Оценка пасты'
        verbose_name_plural = 'Оценки паст'
