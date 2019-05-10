import logging

import fb_auth_token
import requests
import tinder_api
from bson import Binary
from dependencies import Injector, operation
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from config import fb_username, fb_password


def get_logger() -> logging.Logger:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    fh_logger = logging.FileHandler("scraper_logs.log")
    fh_logger.setLevel(logging.DEBUG)

    sh_logger = logging.StreamHandler()
    sh_logger.setLevel(logging.DEBUG)

    logging_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    fh_logger.setFormatter(logging_format)
    sh_logger.setFormatter(logging_format)

    logger.addHandler(fh_logger)
    logger.addHandler(sh_logger)

    return logger


def get_database(host, port, db_name) -> Database:
    client = MongoClient(host, port)
    db = client[db_name]
    return db


class TinderConnector:
    def __init__(self, fb_login: str, fb_password: str, logger: logging.Logger) -> None:
        self.logger = logger
        self.__fb_login = fb_login
        self.__fb_password = fb_password

    def connect(self):
        fb_access_token = fb_auth_token.get_fb_access_token(self.__fb_login, self.__fb_password)
        fb_user_id = fb_auth_token.get_fb_id(fb_access_token)

        tinder_token = tinder_api.get_auth_token(fb_access_token, fb_user_id)
        if tinder_token:
            self.logger.info("Login to Tinder is successful")
        else:
            self.logger.error("Login to Tinder was not successful")


class TinderSaver:
    def __init__(self, db: Database, logger: logging.Logger, collection_name: str = "profiles"):

        self.logger = logger
        self.collection_name = collection_name
        self.db = db
        self.collection: Collection = db[self.collection_name]

    def save_profiles(self):
        recommendations = tinder_api.get_recommendations()
        n_new_profiles = 0
        n_new_photos = 0
        self.logger.info(f"Got {len(recommendations['results'])} recommendations")
        profiles = []
        for res in filter(
            lambda r: self.collection.find_one(filter={"_id": r["_id"]}) is None,
            recommendations["results"],
        ):
            profile = {
                "evaluated": False,
                "distance_mi": res["distance_mi"],
                "_id": res["_id"],
                "bio": res["bio"],
                "birth_date": res["birth_date"],
                "name": res["name"],
                "photos": [],
            }
            n_new_profiles += 1

            for p in res["photos"]:
                url = p["url"]
                response = requests.get(url)
                img = Binary(response.content)
                profile["photos"].append(
                    {"img": img, "filename": p["fileName"], "extension": p["extension"], "url": url}
                )
                n_new_photos += 1
            profiles.append(profile)
        self.logger.info(f"Got {n_new_profiles} new profiles and {n_new_photos} new photos.")
        self.collection.insert_many(profiles)


class TinderContainer(Injector):
    @operation
    def load(saver, connector):
        connector.connect()
        saver.save_profiles()

    saver = TinderSaver
    collection_name = "profiles"
    db = get_database(host=None, port=None, db_name="tinder")
    connector = TinderConnector
    fb_login = fb_username
    fb_password = fb_password
    logger = get_logger()


if __name__ == "__main__":
    TinderContainer.load()
