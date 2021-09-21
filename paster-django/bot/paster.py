import requests
import bs4
from bs4 import BeautifulSoup
import json
import random

from vk_api import keyboard
import config
import time
import traceback

import vk_api
from vk_api.utils import get_random_id
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


def get_timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def is_for_bot(mess):
    return mess.split(' ')[0].split('|')[0] == f'[club{config.group_id}'


def api(url, method='get', data={}):
    if method == 'get':
        response = requests.get(url)
    elif method == 'post':
        response = requests.post(url, data=data)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, features='lxml')
    return json.loads(soup.text)


def paste_keyboard(data={}):
    keyboard = VkKeyboard(inline=True)
    keyboard.add_button('1', color=VkKeyboardColor.NEGATIVE, payload={'paste': data['paste']})
    keyboard.add_button('2', color=VkKeyboardColor.NEGATIVE, payload={'paste': data['paste']})
    keyboard.add_button('3', color=VkKeyboardColor.PRIMARY, payload={'paste': data['paste']})
    keyboard.add_button('4', color=VkKeyboardColor.POSITIVE, payload={'paste': data['paste']})
    keyboard.add_button('5', color=VkKeyboardColor.POSITIVE, payload={'paste': data['paste']})

    keyboard.add_line()

    keyboard.add_button('Паста', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Случайная паста', color=VkKeyboardColor.PRIMARY)
    return keyboard.get_keyboard()


if __name__ == '__main__':
    vk_session = vk_api.VkApi(token=config.token)
    vk = vk_session.get_api()
    longpoll = VkBotLongPoll(vk_session, config.group_id)
    print(get_timestamp(), "Бот запущен!")

    # owner = -108531402

    # max_num = vk.wall.get(owner_id=owner, count=0)['count']
    # for i in range(max_num//100):
    #     tmp = vk.wall.get(owner_id=owner, offset=i, count=100)
    #     print(len(tmp))

    while 1:
        try:
            for event in longpoll.listen():
                if event.type != VkBotEventType.MESSAGE_NEW:
                    continue
                text = event.obj.text
                attaches = event.obj.attachments
                from_id = event.obj.from_id

                if is_for_bot(text):
                    text_ = text.split(' ')[1:]
                    text = ""
                    for t in text_:
                        text += t + " "
                    text = text[:-1]

                if event.from_chat:
                    chat_id = event.chat_id

                    if event.object['attachments'] \
                        and event.object['attachments'][0]['type'] == 'wall' \
                        and event.object['attachments'][0]['wall']['from_id'] in config.groups_minus:
                            group_id = event.object['attachments'][0]['wall']['from_id']
                            wall_id = event.object['attachments'][0]['wall']['id']
                            link = f'https://vk.com/wall{group_id}_{wall_id}'
                            attachment = f'wall{group_id}_{wall_id}'
                            response = api('http://paster-web:8000/api/v1/paste/add/', method='post', data={'link': link})
                            vk.messages.send(
                                chat_id=chat_id, 
                                random_id=get_random_id(), 
                                message='Обнаружена паста\nОцените пожалуйста',
                                attachment=attachment,
                                keyboard=paste_keyboard({'paste': response['id']}),
                            )
                            continue
                    
                    if text.lower() in ('1', '2', '3', '4', '5') and 'payload' in event.object:
                        mark = text.lower()
                        response = api(
                            'http://paster-web:8000/api/v1/paste/relate/', 
                            method='post', 
                            data={
                                'id': json.loads(event.object['payload'])['paste'],
                                'vk_id': from_id,
                                'mark': mark
                            }
                        )
                        if response['status'] == 'ok':
                            vk.messages.send(
                                chat_id=chat_id,  
                                random_id=get_random_id(), 
                                message=f"Успешно оценено на {mark}",
                                reply_to=event.object['id']
                            )
                        else:
                            vk.messages.send(
                                chat_id=chat_id,
                                random_id=get_random_id(), 
                                message=f"Уже оценено",
                                reply_to=event.object['id']
                            )

                    if text.lower() == 'паста':
                        response = api('http://paster-web:8000/api/v1/paste/get/unrelated/')
                        attachment = ''
                        if 'link' in response.keys():
                            group_id = response['link'].split('/')[3].split('-')[1].split('_')[0]
                            wall_id = response['link'].split('/')[3].split('-')[1].split('_')[1]
                            attachment = f'wall-{group_id}_{wall_id}'
                            mess=''
                            vk.messages.send(
                                chat_id=chat_id, 
                                random_id=get_random_id(), 
                                message=mess,
                                keyboard=paste_keyboard({'paste': response['id']}),
                                attachment=attachment
                            )
                        continue

                    if text.lower() == 'случайная паста':
                        response = api('http://paster-web:8000/api/v1/paste/get/rand/')
                        attachment = ''
                        if 'link' in response.keys():
                            group_id = response['link'].split('/')[3].split('-')[1].split('_')[0]
                            wall_id = response['link'].split('/')[3].split('-')[1].split('_')[1]
                            attachment = f'wall-{group_id}_{wall_id}'
                            vk.messages.send(
                                chat_id=chat_id, 
                                random_id=get_random_id(),
                                keyboard=paste_keyboard({'paste': response['id']}),
                                attachment=attachment
                            )
                        continue
                    pass
                else:
                    if event.object['attachments'] \
                        and event.object['attachments'][0]['type'] == 'wall' \
                        and event.object['attachments'][0]['wall']['from_id'] in config.groups_minus:
                            group_id = event.object['attachments'][0]['wall']['from_id']
                            wall_id = event.object['attachments'][0]['wall']['id']
                            link = f'https://vk.com/wall{group_id}_{wall_id}'
                            response = api('http://paster-web:8000/api/v1/paste/add/', method='post', data={'link': link})
                            vk.messages.send(
                                user_id=from_id, 
                                random_id=get_random_id(), 
                                message='Обнаружена паста\nОцените пожалуйста',
                                reply_to=event.obj['id'],
                                keyboard=paste_keyboard({'paste': response['id']}),
                            )
                            continue
                    
                    if text.lower() in ('1', '2', '3', '4', '5') and 'payload' in event.object:
                        mark = text.lower()
                        response = api(
                            'http://paster-web:8000/api/v1/paste/relate/', 
                            method='post', 
                            data={
                                'id': json.loads(event.object['payload'])['paste'],
                                'vk_id': from_id,
                                'mark': mark
                            }
                        )
                        if response['status'] == 'ok':
                            vk.messages.send(
                                user_id=from_id, 
                                random_id=get_random_id(), 
                                message=f"Успешно оценено на {mark}"
                            )
                        else:
                            vk.messages.send(
                                user_id=from_id, 
                                random_id=get_random_id(), 
                                message=f"Уже оценено"
                            )

                    if text.lower() == 'паста':
                        response = api('http://paster-web:8000/api/v1/paste/get/unrelated/')
                        attachment = ''
                        if 'link' in response.keys():
                            group_id = response['link'].split('/')[3].split('-')[1].split('_')[0]
                            wall_id = response['link'].split('/')[3].split('-')[1].split('_')[1]
                            attachment = f'wall-{group_id}_{wall_id}'
                            mess=''
                            vk.messages.send(
                                user_id=from_id, 
                                random_id=get_random_id(), 
                                message=mess,
                                keyboard=paste_keyboard({'paste': response['id']}),
                                attachment=attachment
                            )
                        continue

                    if text.lower() == 'случайная паста':
                        response = api('http://paster-web:8000/api/v1/paste/get/rand/')
                        attachment = ''
                        if 'link' in response.keys():
                            group_id = response['link'].split('/')[3].split('-')[1].split('_')[0]
                            wall_id = response['link'].split('/')[3].split('-')[1].split('_')[1]
                            attachment = f'wall-{group_id}_{wall_id}'
                            vk.messages.send(
                                user_id=from_id, 
                                random_id=get_random_id(),
                                keyboard=paste_keyboard({'paste': response['id']}),
                                attachment=attachment
                            )
                        continue
                    pass
        except Exception as e:
            print(get_timestamp(), 'VK BOT ERROR!')
            traceback.print_exc()
            print(e)