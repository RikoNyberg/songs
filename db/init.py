import datetime
from db.get_db import ColEnum, MongoClientWithDB, create_indexes, get_db
from db.schemas.song import SongBase, SongCreate

def initialize_db(mongo_client: MongoClientWithDB) -> None:
    mongo_client: MongoClientWithDB = get_db()
    mongo_client.db[ColEnum.SONGS].drop()
    mongo_client.db[ColEnum.RATINGS].drop()
    
    test_songs = [
        {"artist": "The Beatles","title": "Lycanthropic Metamorphosis","difficulty": 14.6,"level":13,"released": "2016-10-26"},
        {"artist": "The Beatles","title": "A New Kennel","difficulty": 9.1,"level":9,"released": "2010-02-03"},
        {"artist": "Mr Fastfinger","title": "Awaki-Waki","difficulty": 15,"level":13,"released": "2012-05-11"},
        {"artist": "The Beatles","title": "Beatles've Got The Power","difficulty": 13.22,"level":13,"released": "2014-12-20"},
        {"artist": "The Beatles","title": "Wishing In The Night","difficulty": 10.98,"level":9,"released": "2016-01-01"},
        {"artist": "The Beatles","title": "Opa Opa Ta Bouzoukia","difficulty": 14.66,"level":13,"released": "2013-04-27"},
        {"artist": "The Beatles","title": "Greasy Fingers - boss level","difficulty": 2,"level":3,"released": "2016-03-01"},
        {"artist": "The Beatles","title": "Alabama Sunrise","difficulty": 5,"level":6,"released": "2016-04-01"},
        {"artist": "The Beatles","title": "Can't Buy Me Skills","difficulty": 9,"level":9,"released": "2016-05-01"},
        {"artist": "The Beatles","title": "Vivaldi Allegro Mashup","difficulty": 13,"level":13,"released": "2016-06-01"},
        {"artist": "The Beatles","title": "Babysitting","difficulty": 7,"level":6,"released": "2016-07-01"},
    ]
    mongo_client.db[ColEnum.SONGS].insert_many(
        [
            SongCreate(
                **SongBase(**song).dict(),
                released=datetime.datetime.strptime(song['released'], '%Y-%m-%d'),
            ).dict() for song in test_songs
        ]
    )
    create_indexes(mongo_client)
    