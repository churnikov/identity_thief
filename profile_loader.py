import os
import time
import json
from random import randint

from PIL import Image
import requests
from io import BytesIO

import tinder_api
import fb_auth_token
from config import *


class TinderScraper:

    def __init__(self, fb_login, fb_password, save_path=None):
        self.save_path = save_path or 'Tinder/'
        if not os.path.exists(self.save_path):
            os.mkdir(self.save_path)
        self.ids = set(os.listdir(self.save_path))

        self.__fb_login = fb_login
        self.__fb_password = fb_password

    def init(self):

        fb_access_token = fb_auth_token.get_fb_access_token(self.__fb_login, self.__fb_password)
        fb_user_id = fb_auth_token.get_fb_id(fb_access_token)

        tinder_api.get_auth_token(fb_access_token, fb_user_id)

    def save_profiles(self):
        recommendations = tinder_api.get_recommendations()
        for res in recommendations['results']:
            if res['_id'] not in self.ids:
                self.ids.add(res['_id'])
                path = os.path.join(self.save_path, str(res['_id']))
                os.mkdir(path)
                with open(os.path.join(path, 'info.json'), 'w') as f:
                    json.dump(res, f)
                for p in res['photos']:
                    url = p['processedFiles'][0]['url']
                    img_id = p['id']
                    response = requests.get(url)
                    img = Image.open(BytesIO(response.content))
                    img.save(os.path.join(path, img_id + '.jpg'))


if __name__ == '__main__':
    save_path = '/Volumes/Storage2TB/' + 'tinder_data'
    tin_scraper = TinderScraper(fb_username, fb_password, save_path=save_path)
    tin_scraper.init()
    while True:
        tin_scraper.save_profiles()
        n_sec = randint(120, 320)
        time.sleep(n_sec)
