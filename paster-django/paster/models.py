from datetime import datetime, timedelta, date
import re
from django.utils import timezone
from email.policy import default
import random
from typing import List
from django.db.models.deletion import CASCADE, SET_NULL
import jwt as jwt
from django.contrib.auth.models import AbstractUser
from django.db import models
from configs import settings
from django.db.models import Avg, Sum, Count

from .validators import *

from math import sqrt
import re


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
    name = models.CharField(max_length=75, null=True, blank=True, verbose_name='Имя')
    is_moder = models.BooleanField(default=False, verbose_name='Модератор?')

    def __str__(self) -> str:
        return f"{self.name} ({self.vk_id})"

    @property
    def avg(self) -> float:
        marks = Mark.objects.filter(member=self).aggregate(avg=Avg('mark'))
        if marks['avg']:
            return round(marks['avg'], 2)
        else:
            return 0.0

    @property
    def cnt(self) -> int:
        return Mark.objects.filter(member=self).aggregate(cnt=Count('id'))['cnt']

    class Meta:
        verbose_name = 'Участник'
        verbose_name_plural = 'Участники'


class PasteTag(models.Model):
    """
    [PasteTag]
    Модель тега пасты
    """
    name = models.CharField(max_length=150, verbose_name='Название')

    def __str__(self) -> str:
        return f"{self.name}"

    class Meta:
        verbose_name = 'Тег пасты'
        verbose_name_plural = 'Теги паст'


class Paste(models.Model):
    """
    [Paste]
    Модель пасты
    """
    link = models.CharField(max_length=150, null=True, blank=True, verbose_name='Ссылка на пасту')
    text = models.TextField(null=True, blank=True, verbose_name='Текст пасты')
    last_relate = models.DateTimeField(default=timezone.now)
    sender = models.ForeignKey(Member, on_delete=SET_NULL, null=True, blank=True, verbose_name='Отправитель')
    last_publicate = models.DateTimeField(null=True, blank=True, verbose_name="Дата последней публикации")
    tags = models.ManyToManyField(PasteTag, blank=True, verbose_name="Теги")
    link_self = models.CharField(max_length=150, null=True, blank=True, verbose_name='Ссылка на пасту (в пастере)')
    pic_self = models.CharField(max_length=100, blank=True, null=True, verbose_name="Картинка")
    pic_link_self = models.CharField(max_length=250, blank=True, null=True, verbose_name="Ссылка на картинку")

    @property
    def avg(self) -> float:
        marks = Mark.objects.filter(paste=self).aggregate(avg=Avg('mark'))
        if marks['avg']:
            return round(marks['avg'], 2)
        else:
            return 0.0

    @property
    def cnt(self) -> int:
        return Mark.objects.filter(paste=self).aggregate(cnt=Count('id'))['cnt']

    @property
    def rating(self) -> float:
        marks = Mark.objects.filter(paste=self)
        marks = Mark.objects.filter(paste=self).aggregate(sum=Sum('mark'), cnt=Count('id'))
        if marks['cnt'] == 0:
            return 0
        
        sum_rating = marks['sum']
        n = marks['cnt']
        votes_range = [1, 5]
        z = 1.64485
        v_min = min(votes_range)
        v_width = float(max(votes_range) - v_min)
        phat = (sum_rating - n * v_min) / v_width / float(n)
        rating = (phat+z*z/(2*n)-z*sqrt((phat*(1-phat)+z*z/(4*n))/n))/(1+z*z/n)
        return round(rating * v_width + v_min, 2)

    @property
    def daily_rating(self) -> float:
        marks = Mark.objects.filter(paste=self, created_at__date=date.today()).aggregate(sum=Sum('mark'), cnt=Count('id'))
        if marks['cnt'] == 0:
            return 0
        
        sum_rating = marks['sum']
        n = marks['cnt']
        votes_range = [1, 5]
        z = 1.64485
        v_min = min(votes_range)
        v_width = float(max(votes_range) - v_min)
        phat = (sum_rating - n * v_min) / v_width / float(n)
        rating = (phat+z*z/(2*n)-z*sqrt((phat*(1-phat)+z*z/(4*n))/n))/(1+z*z/n)
        return round(rating * v_width + v_min, 2)

    @property
    def anno(self) -> str:
        result = self.text
        result = re.sub(r"\s+|\n|\r|\s+|\#[a-zA-ZА-Яа-я_0-9]+", ' ', result)
        
        return ' '.join(result.strip().split()[:5]) + '...'

    @property
    def clear_text(self) -> str:
        result = self.text
        result = re.sub(r"\#[a-zA-ZА-Яа-я_0-9]+", ' ', result)
        return result.strip()

    @property
    def group(self) -> str:
        if self.link.startswith('http'):
            return self.link.split('/')[3].split('-')[1].split('_')[0]
        else:
            return ''

    @property
    def post(self) -> str:
        if self.link.startswith('http'):
            return self.link.split('/')[3].split('-')[1].split('_')[1]
        else:
            return ''

    def __str__(self) -> str:
        return f"{self.anno} ({self.link}) ({', '.join([x.name for x in self.tags.all()]) if self.tags.all() else 'NOTAG'})"

    class Meta:
        verbose_name = 'Паста'
        verbose_name_plural = 'Пасты'


class Mark(models.Model):
    """
    [Mark]
    Модель оценки пасты
    """
    member = models.ForeignKey(Member, null=True, blank=True, on_delete=CASCADE)
    paste = models.ForeignKey(Paste, on_delete=CASCADE)
    mark = models.IntegerField(default=5, verbose_name='Оценка')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"{self.member.name} ({self.paste.anno}) ({self.mark})"

    class Meta:
        verbose_name = 'Оценка пасты'
        verbose_name_plural = 'Оценки паст'
        ordering = ('-created_at',)


class ModerAction(models.Model):
    """
    [ModerAction]
    Модель действий модера
    """
    member = models.ForeignKey(Member, null=True, blank=True, on_delete=CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"{self.member.name} ({self.created_at})"

    class Meta:
        verbose_name = 'Действие модера'
        verbose_name_plural = 'Действия модеров'
        ordering = ('-created_at',)


class ModerTag(ModerAction):
    """
    [ModerTag]
    Модель тега модера
    """
    paste = models.ForeignKey(Paste, on_delete=CASCADE, verbose_name='Паста')
    tags = models.ManyToManyField(PasteTag, blank=True, verbose_name="Теги")

    def __str__(self) -> str:
        return f"{self.member.name} ({self.paste.anno}) ({', '.join([x.name for x in self.tags.all()]) if self.tags.all() else 'NOTAG'}) ({self.created_at})"

    class Meta:
        verbose_name = 'Тег модера'
        verbose_name_plural = 'Теги модеров'
        ordering = ('-created_at',)


class Chat(models.Model):
    """
    [Chat]
    Модель чата
    """
    chat_id = models.IntegerField(unique=True, verbose_name='Chat id')
    name = models.CharField(max_length=100, verbose_name='Имя чата')
    messages_enabled = models.BooleanField(default=True, verbose_name='Разрешены сообщения?')

    def __str__(self) -> str:
        return f"{self.name} ({self.chat_id})"

    class Meta:
        indexes = [
            models.Index(fields=['chat_id',]),
        ]
        verbose_name = 'Чат'
        verbose_name_plural = 'Чаты'
