import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import vk_api
import random

from paster.models import *

VK_SERVICE = os.environ.get('VK_SERVICE')
GROUPS = ['108531402', '92157416', '157651636']
VK_OAUTH = os.environ.get('VK_OAUTH')
VK_GROUP_ID = os.environ.get('VK_GROUP_ID')


def get_name_by_id(user_id):
    vk_session = vk_api.VkApi(token=VK_SERVICE)
    vk = vk_session.get_api()
    t = vk.users.get(user_ids=(user_id,), lang='ru')[0]
    print(t)
    return t['first_name'] + ' ' + t['last_name'] 


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
        if not text:
            continue
        link = f'https://vk.com/wall-{group}_{id}'
        paste, created = Paste.objects.get_or_create(link=link, text=text)
        if created:
            paste.save()
            return paste


def get_text_by_id(link):
    vk_session = vk_api.VkApi(token=VK_SERVICE)
    vk = vk_session.get_api()

    group_id = link.split('/')[3].split('-')[1].split('_')[0]
    wall_id = link.split('/')[3].split('-')[1].split('_')[1]
    t = vk.wall.getById(posts=f'-{group_id}_{wall_id}')[0]['text']
    return t


def get_rand_pic(link):
    vk_session = vk_api.VkApi(token=VK_SERVICE)
    vk = vk_session.get_api()

    random.seed(link)

    max_num = vk.photos.get(owner_id=-109290951, album_id='wall', count=0)['count']
    num = random.randint(1, max_num)
    res = ','.join(['photo-' + str(109290951) + '_' + str(
        vk.photos.get(owner_id=str(-109290951), album_id='wall', count=1, offset=num)['items'][0]['id'])])
    
    random.seed()
    return res


def get_rand_pic_link(link):
    vk_session = vk_api.VkApi(token=VK_SERVICE)
    vk = vk_session.get_api()

    random.seed(link)

    max_num = vk.photos.get(owner_id=-109290951, album_id='wall', count=0)['count']
    num = random.randint(1, max_num)
    res = vk.photos.get(owner_id=str(-109290951), album_id='wall', count=1, offset=num)['items'][0].get('sizes')[-1].get('url')
    
    random.seed()
    return res


def get_pic_by_id(link):
    vk_session = vk_api.VkApi(token=VK_SERVICE)
    vk = vk_session.get_api()

    res = ''
    group_id = link.split('/')[3].split('-')[1].split('_')[0]
    wall_id = link.split('/')[3].split('-')[1].split('_')[1]
    att = vk.wall.getById(posts=f'-{group_id}_{wall_id}')[0].get('attachments')
    if att:
        for e in att:
            if e.get('type') == 'photo':
                res += f"photo{e.get('photo').get('owner_id')}_{e.get('photo').get('id')},"
    return res


def get_pic_link_by_id(link):
    vk_session = vk_api.VkApi(token=VK_SERVICE)
    vk = vk_session.get_api()

    group_id = link.split('/')[3].split('-')[1].split('_')[0]
    wall_id = link.split('/')[3].split('-')[1].split('_')[1]
    att = vk.wall.getById(posts=f'-{group_id}_{wall_id}')[0].get('attachments')
    if att and att[0] and att[0].get('photo'):
        return vk.wall.getById(posts=f'-{group_id}_{wall_id}')[0].get('attachments')[0].get('photo').get('sizes')[-1].get('url')
    else:
        return None


def wall_post(message='TEST', copyright=None):
    vk_session = vk_api.VkApi(token=VK_OAUTH)
    vk = vk_session.get_api()

    vk.wall.post(owner_id=f'-{VK_GROUP_ID}', from_group=1, message=message, copyright=copyright)
