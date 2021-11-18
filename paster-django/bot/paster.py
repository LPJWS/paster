import re
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
    keyboard.add_button(config.marks_keys_inv[1], color=VkKeyboardColor.NEGATIVE, payload={'paste': data['paste']})
    keyboard.add_button(config.marks_keys_inv[2], color=VkKeyboardColor.NEGATIVE, payload={'paste': data['paste']})
    keyboard.add_button(config.marks_keys_inv[3], color=VkKeyboardColor.PRIMARY, payload={'paste': data['paste']})
    keyboard.add_button(config.marks_keys_inv[4], color=VkKeyboardColor.POSITIVE, payload={'paste': data['paste']})
    keyboard.add_button(config.marks_keys_inv[5], color=VkKeyboardColor.POSITIVE, payload={'paste': data['paste']})

    keyboard.add_line()

    keyboard.add_button('Паста', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Случайная паста', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('ТОП', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('ТОП Участников', color=VkKeyboardColor.PRIMARY)
    return keyboard.get_keyboard()


def get_name_by_id(user_id):
    t = vk.users.get(user_ids=(user_id,))[0]
    return t['first_name'] + ' ' + t['last_name']


def get_group_by_link(link):
    if not re.match(r'https:\/\/vk\.com\/wall-\d+_\d+', link):
        return None
    else:
        return link.split('/')[3].split('-')[1].split('_')[0]


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
                # print(event)
                if event.type != VkBotEventType.MESSAGE_NEW:
                    continue
                text = event.obj.text
                attaches = event.obj.attachments
                from_id = event.obj.from_id

                if is_for_bot(text):
                    text = text.split(']')[1][1:]

                if event.from_chat:
                    chat_id = event.chat_id
                    mess_id = event.object['conversation_message_id']
                    peer_id = event.object['peer_id']

                    if event.object['attachments']:
                        if event.object['attachments'][0]['type'] == 'wall' \
                        and event.object['attachments'][0]['wall']['from_id'] in config.groups_minus:
                            group_id = event.object['attachments'][0]['wall']['from_id']
                            wall_id = event.object['attachments'][0]['wall']['id']
                            link = f'https://vk.com/wall{group_id}_{wall_id}'
                            # attachment = f'wall{group_id}_{wall_id}'
                            response = api('http://paster-web:8000/api/v1/paste/add/', method='post', data={'link': link, 'vk_id': from_id})
                            vk.messages.send(
                                chat_id=chat_id, 
                                random_id=get_random_id(), 
                                message='Обнаружена паста\nОцените пожалуйста',
                                forward=json.dumps({'peer_id': peer_id, 'is_reply': True, 'conversation_message_ids': [mess_id]}),
                                keyboard=paste_keyboard({'paste': response['id']}),
                            )
                            continue
                        elif event.object['attachments'][0]['type'] == 'link' \
                        and get_group_by_link(event.object['attachments'][0]['link']['url']) in config.groups:
                            response = api('http://paster-web:8000/api/v1/paste/add/', method='post', data={'link': event.object['attachments'][0]['link']['url'], 'vk_id': from_id})
                            vk.messages.send(
                                chat_id=chat_id, 
                                random_id=get_random_id(), 
                                message='Обнаружена паста\nОцените пожалуйста',
                                forward=json.dumps({'peer_id': peer_id, 'is_reply': True, 'conversation_message_ids': [mess_id]}),
                                keyboard=paste_keyboard({'paste': response['id']}),
                            )
                            continue
                    
                    if text in config.marks_keys.keys() and 'payload' in event.object:
                        mark = config.marks_keys[text]
                        paste_id = json.loads(event.object['payload'])['paste']
                        response = api(
                            'http://paster-web:8000/api/v1/paste/relate/', 
                            method='post', 
                            data={
                                'id': paste_id,
                                'vk_id': from_id,
                                'mark': mark
                            }
                        )
                        paste_response = api(f'http://paster-web:8000/api/v1/paste/get/{paste_id}/')
                        if response['status'] == 'ok':
                            vk.messages.send(
                                chat_id=chat_id,  
                                random_id=get_random_id(), 
                                message=f"[id{from_id}|Вы] успешно оценили пасту \"{paste_response['anno']}\" на {mark}⭐️",
                            )
                        else:
                            vk.messages.send(
                                chat_id=chat_id,
                                random_id=get_random_id(), 
                                message=f"[id{from_id}|Вы] уже оценили пасту \"{paste_response['anno']}\"!",
                            )

                    if text.lower() == 'паста':
                        response = api(f'http://paster-web:8000/api/v1/paste/get/unrelated/?vk_id={from_id}')
                        attachment = ''
                        if 'link' in response.keys():
                            group_id = response['link'].split('/')[3].split('-')[1].split('_')[0]
                            wall_id = response['link'].split('/')[3].split('-')[1].split('_')[1]
                            rating = response['rating']
                            cnt = response['cnt']
                            attachment = f'wall-{group_id}_{wall_id}'
                            mess = f'Данную пасту оценили {cnt} раз, рейтинг - {rating}⭐️'
                            if response['sender']:
                                mess += f'\nПасту прислал [id{response["sender"]["id"]}|{response["sender"]["name"]}]'
                            vk.messages.send(
                                chat_id=chat_id, 
                                random_id=get_random_id(), 
                                message=mess,
                                keyboard=paste_keyboard({'paste': response['id']}),
                                attachment=attachment
                            )
                        continue

                    if text.lower() == 'случайная паста':
                        response = api(f'http://paster-web:8000/api/v1/paste/get/rand/?vk_id={from_id}')
                        attachment = ''
                        if 'link' in response.keys():
                            group_id = response['link'].split('/')[3].split('-')[1].split('_')[0]
                            wall_id = response['link'].split('/')[3].split('-')[1].split('_')[1]
                            rating = response['rating']
                            cnt = response['cnt']
                            attachment = f'wall-{group_id}_{wall_id}'
                            mess = f'Данную пасту оценили {cnt} раз, рейтинг - {rating}⭐️'
                            if response['sender']:
                                mess += f'\nПасту прислал [id{response["sender"]["id"]}|{response["sender"]["name"]}]'
                            vk.messages.send(
                                chat_id=chat_id, 
                                random_id=get_random_id(),
                                keyboard=paste_keyboard({'paste': response['id']}),
                                attachment=attachment,
                                message=mess
                            )
                        continue

                    if text.lower() == 'топ':
                        response = api('http://paster-web:8000/api/v1/paste/get/top/')
                        mess = "Лучшие пасты:\n\nПаста - рейтинг - кол-во оценок\n\n"
                        i = 1
                        for paste in response:
                            mess += f"{i}. [{paste['link']}|{paste['anno']}] {paste['rating']}⭐️ {paste['cnt']}🧮\n\n"
                            i += 1
                        vk.messages.send(
                            chat_id=chat_id, 
                            random_id=get_random_id(),
                            message=mess,
                            keyboard=config.main_keyboard
                        )
                        continue

                    if text.lower() == 'топ участников':
                        response = api('http://paster-web:8000/api/v1/member/get/top/')
                        mess = "Лучшие участники:\n\nУчастник - кол-во оценок - средняя оценка\n\n"
                        i = 1
                        for member in response:
                            mess += f"{i}. [id{member['vk_id']}|{member['name']}] {member['cnt']}🧮 {member['avg']}⭐️\n\n"
                            i += 1
                        vk.messages.send(
                            chat_id=chat_id, 
                            random_id=get_random_id(),
                            message=mess,
                            keyboard=config.main_keyboard
                        )
                        continue

                    if text.lower() == 'начать':
                        vk.messages.send(
                            chat_id=chat_id, 
                            random_id=get_random_id(),
                            keyboard=config.main_keyboard,
                            message='Чего хочешь, дорогой? Инфа если что есть на стене'
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
                            response = api('http://paster-web:8000/api/v1/paste/add/', method='post', data={'link': link, 'vk_id': from_id})
                            vk.messages.send(
                                user_id=from_id, 
                                random_id=get_random_id(), 
                                message='Обнаружена паста\nОцените пожалуйста',
                                reply_to=event.obj['id'],
                                keyboard=paste_keyboard({'paste': response['id']}),
                            )
                            continue
                    
                    if text in config.marks_keys.keys() and 'payload' in event.object:
                        mark = config.marks_keys[text]
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
                                message=f"Успешно оценено на {mark}⭐️"
                            )
                        else:
                            vk.messages.send(
                                user_id=from_id, 
                                random_id=get_random_id(), 
                                message=f"Уже оценено"
                            )

                    if text.lower() == 'паста':
                        response = api(f'http://paster-web:8000/api/v1/paste/get/unrelated/?vk_id={from_id}')
                        attachment = ''
                        if 'link' in response.keys():
                            group_id = response['link'].split('/')[3].split('-')[1].split('_')[0]
                            wall_id = response['link'].split('/')[3].split('-')[1].split('_')[1]
                            rating = response['rating']
                            cnt = response['cnt']
                            attachment = f'wall-{group_id}_{wall_id}'
                            mess = f'Данную пасту оценили {cnt} раз, рейтинг - {rating}⭐️'
                            if response['sender']:
                                mess += f'\nПасту прислал [id{response["sender"]["id"]}|{response["sender"]["name"]}]'
                            vk.messages.send(
                                user_id=from_id, 
                                random_id=get_random_id(), 
                                message=mess,
                                keyboard=paste_keyboard({'paste': response['id']}),
                                attachment=attachment
                            )
                        continue

                    if text.lower() == 'случайная паста':
                        response = api(f'http://paster-web:8000/api/v1/paste/get/rand/?vk_id={from_id}')
                        attachment = ''
                        if 'link' in response.keys():
                            group_id = response['link'].split('/')[3].split('-')[1].split('_')[0]
                            wall_id = response['link'].split('/')[3].split('-')[1].split('_')[1]
                            rating = response['rating']
                            cnt = response['cnt']
                            attachment = f'wall-{group_id}_{wall_id}'
                            mess = f'Данную пасту оценили {cnt} раз, рейтинг - {rating}⭐️'
                            if response['sender']:
                                mess += f'\nПасту прислал [id{response["sender"]["id"]}|{response["sender"]["name"]}]'
                            vk.messages.send(
                                user_id=from_id, 
                                random_id=get_random_id(),
                                keyboard=paste_keyboard({'paste': response['id']}),
                                attachment=attachment,
                                message=mess
                            )
                        continue

                    if text.lower() == 'топ':
                        response = api('http://paster-web:8000/api/v1/paste/get/top/')
                        mess = "Лучшие пасты:\n\nПаста - рейтинг - кол-во оценок\n\n"
                        i = 1
                        for paste in response:
                            mess += f"{i}. [{paste['link']}|{paste['anno']}] {paste['rating']}⭐️ {paste['cnt']}🧮\n\n"
                            i += 1
                        vk.messages.send(
                            user_id=from_id, 
                            random_id=get_random_id(),
                            message=mess,
                            keyboard=config.main_keyboard
                        )
                        continue
                    pass

                    if text.lower() == 'топ участников':
                        response = api('http://paster-web:8000/api/v1/member/get/top/')
                        mess = "Лучшие участники:\n\nУчастник - кол-во оценок - средняя оценка\n\n"
                        i = 1
                        for member in response:
                            mess += f"{i}. [id{member['vk_id']}|{member['name']}] {member['cnt']}🧮 {member['avg']}⭐️\n\n"
                            i += 1
                        vk.messages.send(
                            user_id=from_id, 
                            random_id=get_random_id(),
                            message=mess,
                            keyboard=config.main_keyboard
                        )
                        continue
                        
                    vk.messages.send(
                            user_id=from_id, 
                            random_id=get_random_id(),
                            keyboard=config.main_keyboard,
                            message='Чего хочешь, дорогой? Инфа если что есть на стене'
                        )
        except Exception as e:
            print(get_timestamp(), 'VK BOT ERROR!')
            traceback.print_exc()
            print(e)