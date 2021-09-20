import requests
import bs4
from bs4 import BeautifulSoup
import json
import random
import config
import time
import traceback

import vk_api
from vk_api.utils import get_random_id
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


def get_timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


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

                if event.from_chat:
                    chat_id = event.chat_id
                    vk.messages.send(chat_id=chat_id, random_id=get_random_id(), message=text)
                else:
                    response = requests.get('http://paster-web:8000/api/v1/test/test/')
                    response.encoding = 'utf-8'
                    soup = BeautifulSoup(response.text)
                    print(soup, features='lxml')
                    vk.messages.send(user_id=from_id, random_id=get_random_id(), message=text)
        except Exception as e:
            print(get_timestamp(), 'VK BOT ERROR!')
            traceback.print_exc()
            print(e)