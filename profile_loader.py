import os
import time
import json
from random import randint
import logging

from PIL import Image
import requests
from io import BytesIO

import tinder_api
import fb_auth_token
from config import *

logger = logging.getLogger('tinder_scraper')
logger.setLevel(logging.DEBUG)

fh_logger = logging.FileHandler('scraper_logs.log')
fh_logger.setLevel(logging.DEBUG)

sh_logger = logging.StreamHandler()
sh_logger.setLevel(logging.ERROR)

logging_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh_logger.setFormatter(logging_format)
sh_logger.setFormatter(logging_format)

logger.addHandler(fh_logger)
logger.addHandler(sh_logger)

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

        tinder_token = tinder_api.get_auth_token(fb_access_token, fb_user_id)
        if tinder_token:
            logging.info('Login to Tinder is successful')
        else:
            logging.error('Login to Tinder was not successful')

    def save_profiles(self):
        recommendations = tinder_api.get_recommendations()
        n_new_profiles = 0
        n_new_photos = 0
        logging.info(f'Got {len(recommendations["results"])} recommendations')
        for res in recommendations['results']:
            if res['_id'] not in self.ids:
                n_new_profiles += 1
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
                    n_new_photos += 1
        logging.info(f'Got {n_new_profiles} new profiles and {n_new_photos} new photos.')


if __name__ == '__main__':
    with open('config.json', 'r') as f:
        save_path = json.load(f)['tinder_scraper']['save_path']
    tin_scraper = TinderScraper(fb_username, fb_password, save_path=save_path)
    tin_scraper.init()
    while True:
        tin_scraper.save_profiles()
        n_sec = randint(120, 320)
        logging.info(f'Sleep for {n_sec} seconds')
        time.sleep(n_sec)
