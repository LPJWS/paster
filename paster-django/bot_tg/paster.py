import re
from django.test import tag
import requests
from bs4 import BeautifulSoup
import json
import random

from config import Config
import time


def get_timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def api(url, method='get', data={}):
    if method == 'get':
        response = requests.get(url)
    elif method == 'post':
        response = requests.post(url, data=data)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, features='lxml')
    return json.loads(soup.text)



if __name__ == '__main__':
    while True:
        continue