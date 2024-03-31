import telebot
from telebot import types
from config import settings
import requests


def api(url, method='get', data={}):
    if method == 'get':
        response = requests.get(url)
    elif method == 'post':
        response = requests.post(url, data=data)
    return response.json()


bot = telebot.TeleBot(settings.TG_TOKEN)


@bot.message_handler(commands=['start'])
def start(message: types.Message):
    user_id = message.from_user.id
    nickname = message.from_user.full_name
    reply = f"Привет, {nickname}\n\nПрисылай текст своей пасты (помни про ограничения на длину сообщений ТГ в 4096 символов)\nПроставь хэштеги прямо в тексте (обязательно через #), либо модераторы проставят их сами исходя из содержания\nКартинки пока не поддерживаются, подставится рандомная, но это обязательно будет исправлено"
    bot.send_message(user_id, reply)


@bot.message_handler(content_types=['text'])
def get_text_messages(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    api('http://paster-web:8000/api/v1/wall/suggests/add/', method='post', data={'text': message.text, 'sender': user_id, 'sender_nickname': username})
    reply = "Принято, рассмотрим в ближайшее время"
    bot.send_message(user_id, reply)
    bot.send_message(settings.ADMIN_ID, "Новая паста пришла, чекни")


if __name__ == '__main__':
    print("TG-Bot started")
    bot.infinity_polling()
