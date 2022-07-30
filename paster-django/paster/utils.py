import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import vk_api
import random
import urllib.request
import requests
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from paster.models import *


VK_SERVICE = os.environ.get('VK_SERVICE')
GROUPS = ['108531402', '92157416', '157651636']
VK_OAUTH = os.environ.get('VK_OAUTH')
VK_GROUP_ID = os.environ.get('VK_GROUP_ID')
VK_TOKEN = os.environ.get('VK_TOKEN')


def get_name_by_id(user_id):
    vk_session = vk_api.VkApi(token=VK_SERVICE)
    vk = vk_session.get_api()
    t = vk.users.get(user_ids=(user_id,), lang='ru')[0]
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


def get_suggests():
    vk_session = vk_api.VkApi(token=VK_OAUTH)
    vk = vk_session.get_api()

    res = vk.wall.get(owner_id=f"-{os.environ.get('VK_GROUP_ID')}", filter='suggests')
    if res.get('items'):
        try:
            member = Member.objects.get(vk_id=res['items'][-1]['from_id'])
        except Member.DoesNotExist:
            member = Member.objects.create(vk_id=res['items'][-1]['from_id'])
            member.name = get_name_by_id(res['items'][-1]['from_id'])
            member.save()
        if res['items'][-1].get('attachments'):
            if res['items'][-1].get('attachments')[0]['type'] == 'photo':
                return {'count': res['count'], 'item': res['items'][-1], 'member': {'id': member.vk_id, 'name': member.name}, 'photo': res['items'][-1].get('attachments')[0]['photo']['sizes'][-1].get('url')}
        return {'count': res['count'], 'item': res['items'][-1], 'member': {'id': member.vk_id, 'name': member.name}}
    else:
        return {'count': 0}


def post_suggest(post_id, tags):
    vk_session = vk_api.VkApi(token=VK_OAUTH)
    vk = vk_session.get_api()

    post = vk.wall.getById(posts=f"-{os.environ.get('VK_GROUP_ID')}_{post_id}")
    try:
        member = Member.objects.get(vk_id=post[0]['from_id'])
    except Member.DoesNotExist:
        member = Member.objects.create(vk_id=post[0]['from_id'])
        member.name = get_name_by_id(post[0]['from_id'])
        member.save()
    paste = Paste.objects.create(sender=member, text=post[0]['text'], link=''.join(random.choices('qwertyuiopasdfghjklzxcvbnm1234567890', k=10)))
    for tag in tags:
        paste.tags.add(tag)
    paste.save()

    tags_ = paste.tags.all()
    if not tags_:
        tags_ = '\n#пастер_рандом'
    else:
        tags_ = '\n' + '\n'.join(map(lambda x: '#пастер_' + x.name.lower(), tags_))
    message = f'#пастер_предложка'
    message += tags_
    message += f'\nОценить пасту: https://vk.com/app7983387#{paste.id}'
    if paste.sender:
        message += f'\nПасту прислал [id{paste.sender.vk_id}|{paste.sender.name}]'
    message += f'\n\n{paste.clear_text}'

    if post[0].get('attachments'):
        if post[0].get('attachments')[0]['type'] == 'photo':
            rand_link = post[0].get('attachments')[0]['photo']['sizes'][-1].get('url')
        else:
            rand_link = get_rand_pic_link(paste.link)
    else:
        rand_link = get_rand_pic_link(paste.link)
    urllib.request.urlretrieve(rand_link, settings.MEDIA_ROOT + "local-filename.jpg")
    a = vk.photos.getAlbums(owner_id=f"-{os.environ.get('VK_GROUP_ID')}")
    server = vk.photos.getUploadServer(album_id=a['items'][0]['id'], group_id=os.environ.get('VK_GROUP_ID'))['upload_url']
    pfile = requests.post(server, files={'file1': open(settings.MEDIA_ROOT + 'local-filename.jpg', 'rb')}).json()
    photo = vk.photos.save(album_id=a['items'][0]['id'], server=pfile['server'], photos_list=pfile['photos_list'], hash=pfile['hash'], group_id=pfile['gid'])[0]
    paste.pic_self = f"photo{photo['owner_id']}_{photo['id']}"
    paste.pic_link_self = photo.get('sizes')[-1].get('url')
    paste.save()

    res = vk.wall.post(owner_id=f"-{os.environ.get('VK_GROUP_ID')}", post_id=post_id, signed=1, message=message, attachments=paste.pic_self)
    return res


def deny_suggest(post_id):
    vk_session = vk_api.VkApi(token=VK_OAUTH)
    vk = vk_session.get_api()

    res = vk.wall.delete(owner_id=f"-{os.environ.get('VK_GROUP_ID')}", post_id=post_id)
    return res


def get_chat_name(_chat_id):
    vk_session = vk_api.VkApi(token=VK_TOKEN)
    vk = vk_session.get_api()
    try:
        res = vk.messages.getConversationsById(peer_ids=[2000000000 + _chat_id], group_id=os.environ.get('VK_GROUP_ID'))['items'][0][
        'chat_settings']['title']
    except Exception:
        res = 'NONAME'
    return res


def get_enable_keyboard():
    keyboard = VkKeyboard(inline=True)
    keyboard.add_button('Отключить уведомления', color=VkKeyboardColor.PRIMARY)
    return keyboard.get_keyboard()