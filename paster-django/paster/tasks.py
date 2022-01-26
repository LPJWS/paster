from email import message
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
import urllib.request


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
    if best.daily_rating == 0:
        regular_post.delay()
        return
    serializer = PasteSerializer(instance=best).data

    tags = serializer.get('tags')
    if not tags:
        tags = '\n#пастер_рандом'
    else:
        tags = '\n' + '\n'.join(map(lambda x: '#пастер_' + x['name'].lower(), tags))
    message = f'#пастер_топдня'
    message += tags
    message += f'\nЛучшая паста за день ({date.today().day}.{date.today().month}):'
    if best.sender:
        message += f'\nПасту прислал [id{best.sender.vk_id}|{best.sender.name}]'
    message += f'\n\n{best.clear_text}'
    copyright = best.link
    if not best.pic_self:
        urllib.request.urlretrieve(serializer.get('pic_link'), settings.MEDIA_ROOT + "local-filename.jpg")
        a = vk.photos.getAlbums(owner_id=f"-{os.environ.get('VK_GROUP_ID')}")
        server = vk.photos.getUploadServer(album_id=a['items'][0]['id'], group_id=os.environ.get('VK_GROUP_ID'))['upload_url']
        pfile = requests.post(server, files={'file1': open(settings.MEDIA_ROOT + 'local-filename.jpg', 'rb')}).json()
        photo = vk.photos.save(album_id=a['items'][0]['id'], server=pfile['server'], photos_list=pfile['photos_list'], hash=pfile['hash'], group_id=pfile['gid'])[0]
        best.pic_self = f"photo{photo['owner_id']}_{photo['id']}"
        best.pic_link_self = photo.get('sizes')[-1].get('url')
        best.save()
    attach = best.pic_self

    # vk.wall.post(owner_id=f'-{VK_GROUP_ID}', from_group=1, message=message, copyright=copyright, attachment=attach)
    vk.wall.post(owner_id=f'-{VK_GROUP_ID}', from_group=1, message=message, attachment=attach)
    best.last_publicate = timezone.now()
    best.link_self = f"https://vk.com/wall-{os.environ.get('VK_GROUP_ID')}_{res['post_id']}"
    best.save()


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
    serializer = PasteSerializer(instance=best).data

    tags = serializer.get('tags')
    if not tags:
        tags = '\n#пастер_рандом'
    else:
        tags = '\n' + '\n'.join(map(lambda x: '#пастер_' + x['name'].lower(), tags))
    message = tags
    message += f'\nОценить пасту: https://vk.com/app7983387#{best.id}'
    if best.sender:
        message += f'\nПасту прислал [id{best.sender.vk_id}|{best.sender.name}]'
    message += f'\n\n{best.clear_text}'
    copyright = best.link
    if not best.pic_self:
        urllib.request.urlretrieve(serializer.get('pic_link'), settings.MEDIA_ROOT + "local-filename.jpg")
        a = vk.photos.getAlbums(owner_id=f"-{os.environ.get('VK_GROUP_ID')}")
        server = vk.photos.getUploadServer(album_id=a['items'][0]['id'], group_id=os.environ.get('VK_GROUP_ID'))['upload_url']
        pfile = requests.post(server, files={'file1': open(settings.MEDIA_ROOT + 'local-filename.jpg', 'rb')}).json()
        photo = vk.photos.save(album_id=a['items'][0]['id'], server=pfile['server'], photos_list=pfile['photos_list'], hash=pfile['hash'], group_id=pfile['gid'])[0]
        best.pic_self = f"photo{photo['owner_id']}_{photo['id']}"
        best.pic_link_self = photo.get('sizes')[-1].get('url')
        best.save()
    attach = best.pic_self

    # vk.wall.post(owner_id=f'-{VK_GROUP_ID}', from_group=1, message=message, copyright=copyright, attachment=attach)
    res = vk.wall.post(owner_id=f'-{VK_GROUP_ID}', from_group=1, message=message, attachment=attach)
    best.last_publicate = timezone.now()
    best.link_self = f"https://vk.com/wall-{os.environ.get('VK_GROUP_ID')}_{res['post_id']}"
    best.save()
