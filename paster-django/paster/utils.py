import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import vk_api
import random

from paster.models import *

VK_SERVICE = os.environ.get('VK_SERVICE')
GROUPS = ['108531402', '92157416']

def send_email(m: str, to: str, s: str):
    msg = MIMEMultipart()

    password = os.environ.get('EMAIL_PASSWORD')
    msg['From'] = os.environ.get('EMAIL_LOGIN')
    msg['To'] = to
    msg['Subject'] = s

    msg.attach(MIMEText(m, 'plain'))

    server = smtplib.SMTP('smtp.yandex.ru', 587)
    server.starttls()
    server.login(msg['From'], password)
    server.sendmail(msg['From'], msg['To'], msg.as_string())
    server.quit()


def accumulate():
    vk_session = vk_api.VkApi(token=VK_SERVICE)
    vk = vk_session.get_api()
    
    while True:
        group = random.choice(GROUPS)
        max_num = vk.wall.get(owner_id=-int(group), count=0)['count']
        num = random.randint(1, max_num)
        t = vk.wall.get(owner_id=-int(group), count=1, offset=num)
        id = t['items'][0]['id']
        text = t['items'][0]['text']
        link = f'https://vk.com/wall-{group}_{id}'
        paste, created = Paste.objects.get_or_create(link=link, text=text)
        if created:
            paste.save()
            break


def get_text_by_id(link):
    vk_session = vk_api.VkApi(token=VK_SERVICE)
    vk = vk_session.get_api()

    group_id = link.split('/')[3].split('-')[1].split('_')[0]
    wall_id = link.split('/')[3].split('-')[1].split('_')[1]
    t = vk.wall.getById(posts=f'-{group_id}_{wall_id}')[0]['text']
    return t
