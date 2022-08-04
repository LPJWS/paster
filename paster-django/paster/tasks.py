from email import message
import requests
from celery import shared_task

from configs import settings
from configs.celery import app

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

from paster.models import User, Paste, Chat
from paster.serializers import PasteSerializer

from datetime import datetime, timedelta, date
import vk_api
from vk_api.utils import get_random_id
from django.db.models import Q
from django.utils import timezone
import urllib.request
import paster.utils


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
    VK_TOKEN = os.environ.get('VK_TOKEN')
    vk_session = vk_api.VkApi(token=VK_OAUTH)
    vk = vk_session.get_api()
    vk_session_bot = vk_api.VkApi(token=VK_TOKEN)
    vk_bot = vk_session_bot.get_api()
    
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
    day, month = date.today().day, date.today().month
    message += f'\nЛучшая паста за день ({day if day > 9 else "0" + str(day)}.{month if month > 9 else "0" + str(month)}):'
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

    chats = Chat.objects.filter(messages_enabled=True)
    for chat in chats:
        try:
            vk_bot.messages.send(
                chat_id=chat.chat_id, 
                random_id=get_random_id(),
                message="Паста дня",
                keyboard=paster.utils.get_enable_keyboard(),
                attachment=f"wall-{os.environ.get('VK_GROUP_ID')}_{res['post_id']}"
            )
        except Exception:
            continue

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
    best = Paste.objects.filter(Q(last_publicate__isnull=True) & ~Q(tags=None))
    if best:
        best = best[0]
    else:
        best = sorted(Paste.objects.filter(Q(last_publicate__isnull=False) & ~Q(tags=None)), key=lambda t: t.last_publicate)[0]
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
