from enum import Enum
import os
import datetime
from typing import Optional
from pymongo import MongoClient, TEXT

class ColEnum(str, Enum):
    SONGS = "songs"
    RATINGS = "ratings"

class MongoClientWithDB:
    def __init__(self):
        self.client = MongoClient()
        self.db = self.client[get_db_name()]


PERSISTENT_DB_CLIENT: Optional[MongoClient] = None
def get_db() -> MongoClient:
    global PERSISTENT_DB_CLIENT
    if PERSISTENT_DB_CLIENT is None:
        PERSISTENT_DB_CLIENT = MongoClientWithDB()
    return PERSISTENT_DB_CLIENT


def get_db_name() -> str:
    return "songs_db" if ("PYTEST_CURRENT_TEST" not in os.environ) else "songs_db_test"


def fix_released_date_to_datetime(mongo_client: MongoClientWithDB):
    for song in mongo_client.db.songs.find():
        if type(song['released']) is not datetime.datetime:
            mongo_client.db.songs.find_one_and_update(
                {'_id': song['_id']}, 
                {'$set': {
                    'released': datetime.datetime.strptime(song['released'], '%Y-%m-%d'),
                }}
            )

def create_indexes(mongo_client: MongoClientWithDB):
    mongo_client.db[ColEnum.RATINGS].create_index("song_id")
    mongo_client.db[ColEnum.SONGS].create_index('level')
    mongo_client.db[ColEnum.SONGS].create_index(
        [   
            ('artist', TEXT),
            ('title', TEXT),
        ], 
        default_language='english'
    )

fix_released_date_to_datetime(get_db())
create_indexes(get_db())