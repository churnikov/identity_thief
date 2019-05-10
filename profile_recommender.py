from dependencies import Injector
from pymongo.collection import Collection
from pymongo.database import Database

from profile_loader import get_database, TinderContainer


class SimpleRecommender:
    def __init__(self, db: Database, collection_name: str):
        self.collection_name = collection_name
        self.db = db
        self.collection: Collection = self.db[self.collection_name]

    def __call__(self):
        res = self.collection.find_one({"evaluated": False})
        if res is None:
            TinderContainer.load()
            res = self.__call__()
        return res


class Evaluate:
    def __init__(self, db: Database, collection_name: str):
        self.collection_name = collection_name
        self.db = db
        self.collection: Collection = self.db[self.collection_name]

    def __call__(self, profile, is_like: bool):
        profile["evaluated"] = True
        profile["like"] = is_like
        self.collection.find_one_and_replace({"_id": profile["_id"]}, profile)


class Recommender(Injector):
    recommend = SimpleRecommender
    collection_name = "profiles"
    db = get_database(host=None, port=None, db_name="tinder")


class Marker(Injector):
    mark = Evaluate
    collection_name = "profiles"
    db = get_database(host=None, port=None, db_name="tinder")
