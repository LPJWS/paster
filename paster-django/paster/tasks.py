import requests
from celery import shared_task

from configs import settings
from configs.celery import app

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

from paster.models import User, Paste
from paster.serializers import PasteSerializer

from datetime import datetime, timedelta, date
import vk_api
from django.db.models import Q
from django.utils import timezone


@app.task()
def send_email(m: str, to: str, s: str):
    msg = MIMEMultipart()

    password = os.environ.get('EMAIL_PASSWORD')
    msg['From'] = os.environ.get('EMAIL_LOGIN')
    msg['To'] = to
    msg['Subject'] = s
    print(password, msg)

    msg.attach(MIMEText(m, 'plain'))

    server = smtplib.SMTP('smtp.yandex.ru', 587)
    server.starttls()
    server.login(msg['From'], password)
    server.sendmail(msg['From'], msg['To'], msg.as_string())
    server.quit()


@app.task()
def daily_post():
    VK_OAUTH = os.environ.get('VK_OAUTH')
    VK_GROUP_ID = os.environ.get('VK_GROUP_ID')
    vk_session = vk_api.VkApi(token=VK_OAUTH)
    vk = vk_session.get_api()
    
    best = sorted(Paste.objects.all(), key=lambda t: t.daily_rating, reverse=True)[0]
    serializer = PasteSerializer(instance=best).data

    message = f'#пастер_топдня\nЛучшая паста за день ({date.today().day}.{date.today().month}):'
    if best.sender:
        message += f'\nПасту прислал [id{best.sender.vk_id}|{best.sender.name}]'
    message += f'\n\n{best.clear_text}'
    copyright = best.link
    attach = serializer.get('pic')

    # vk.wall.post(owner_id=f'-{VK_GROUP_ID}', from_group=1, message=message, copyright=copyright, attachment=attach)
    vk.wall.post(owner_id=f'-{VK_GROUP_ID}', from_group=1, message=message, attachment=attach)


@app.task()
def regular_post():
    VK_OAUTH = os.environ.get('VK_OAUTH')
    VK_GROUP_ID = os.environ.get('VK_GROUP_ID')
    vk_session = vk_api.VkApi(token=VK_OAUTH)
    vk = vk_session.get_api()
    
    # time_threshold = datetime.now(timezone.now()) - timedelta(days=14)
    best = Paste.objects.filter(Q(last_publicate__isnull=True))
    if best:
        best = best[0]
    else:
        best = sorted(Paste.objects.filter(Q(last_publicate__isnull=False)), key=lambda t: t.last_publicate)[0]
    best.last_publicate = timezone.now()
    best.save()
    serializer = PasteSerializer(instance=best).data

    message = f'#пастер_рандом\nОценить пасту: https://vk.com/app7983387#{best.id}'
    if best.sender:
        message += f'\nПасту прислал [id{best.sender.vk_id}|{best.sender.name}]'
    message += f'\n\n{best.clear_text}'
    copyright = best.link
    attach = serializer.get('pic')

    # vk.wall.post(owner_id=f'-{VK_GROUP_ID}', from_group=1, message=message, copyright=copyright, attachment=attach)
    vk.wall.post(owner_id=f'-{VK_GROUP_ID}', from_group=1, message=message, attachment=attach)

