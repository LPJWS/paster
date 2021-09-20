import requests
import bs4
from bs4 import BeautifulSoup
import json
import random
import config
import vk_api


if __name__ == '__main__':
    vk_session = vk_api.VkApi(token=config.token)
    vk = vk_session.get_api()

    # owner = -108531402

    # max_num = vk.wall.get(owner_id=owner, count=0)['count']
    # for i in range(max_num//100):
    #     tmp = vk.wall.get(owner_id=owner, offset=i, count=100)
    #     print(len(tmp))
    