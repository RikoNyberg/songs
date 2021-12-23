import asyncio
from typing import Optional

from fastapi.exceptions import HTTPException
from db.init import initialize_db

from db.schemas.song import SongInDB
from router import (
    add_song_rating,
    get_song_rating,
    get_songs,
    get_songs_average_difficulty,
)
from app.schemas.rating import RatingGet, RatingPostConfirmation, RatingPostConfirmationResultEnum
from db.get_db import ColEnum, MongoClientWithDB, get_db
from db.schemas.rating import RatingInDB
import pytest
from pydantic import ValidationError

@pytest.fixture(scope="session", autouse=True)
def execute_before_any_test() -> None:
    initialize_db(get_db())


@pytest.fixture(scope="module")
def test_mongo_client() -> MongoClientWithDB:
    return get_db()


@pytest.mark.parametrize(
    "offset,limit,song_count",
    [
        (None, None, 11),
        (2, None, 9),
        (None, 2, 2),
        (2, 2, 2),
        (2, 10, 9),
        (20, None, 0),
        (None, 20, 11),
    ],
)
def test_get_songs(
    test_mongo_client: MongoClientWithDB,
    offset: Optional[int],
    limit: Optional[int],
    song_count: int,
):

    offset_and_limit = {}
    if offset is not None and limit is None:
        offset_and_limit = {'offset':offset}
    elif offset is None and limit is not None:
        offset_and_limit = {'limit':limit}
    elif offset is not None and limit is not None:
        offset_and_limit = {'offset':offset, 'limit':limit}

    assert len(asyncio.new_event_loop().run_until_complete(
        get_songs(
            **offset_and_limit, mongo_client=test_mongo_client
        )
    )) == song_count


@pytest.mark.parametrize(
    "level,average_difficulty",
    [
        (13, 14.096),
        (9, 9.693),
        (6, 6),
        (3, 2),
        (100, 0.0),
    ],
)
def test_get_songs_average_difficulty(
    test_mongo_client: MongoClientWithDB,
    level: Optional[int], average_difficulty: float):
    assert asyncio.new_event_loop().run_until_complete(
        get_songs_average_difficulty(level=level, mongo_client=test_mongo_client)
    ) == average_difficulty or pytest.approx(average_difficulty, 0.001)


@pytest.mark.parametrize(
    "search,count,artist",
    [
        ("Awaki-Waki", 1, "Mr Fastfinger"),
        ("waki", 1, "Mr Fastfinger"),
        ("Fast", 1, "Mr Fastfinger"),
        ("The", 10, "The Beatles"),
        ("beatles", 10, "The Beatles"),
        ("ä", 0, None),
        # NOTE: following searches are not found 
        #       with the text index search:
        ("Beat", 10, "The Beatles"),
        ("Th", 10, "The Beatles"),
        ("The Beat", 10, "The Beatles"),
        ("eatl", 10, "The Beatles"),
        ("a", 11, None),
        ("", 11, None),
    ],
)
def test_get_songs_search(
    test_mongo_client: MongoClientWithDB,
    search: str,
    count: float,
    artist: Optional[str],
):
    search_results = asyncio.new_event_loop().run_until_complete(
        get_songs(message=search, mongo_client=test_mongo_client)
    )

    assert len(search_results) == count
    if artist:
        assert search_results[0].artist == artist


@pytest.mark.parametrize("rating", list(range(1, 6)))
def test_add_song_rating(
    test_mongo_client: MongoClientWithDB,
    rating: int,
):
    song: SongInDB = SongInDB(**test_mongo_client.db[ColEnum.SONGS].find_one())

    response = asyncio.new_event_loop().run_until_complete(
        add_song_rating(
            song_id=str(song.id),
            rating=rating,
            mongo_client=test_mongo_client,
        )
    )
    assert response == RatingPostConfirmation(result=RatingPostConfirmationResultEnum.SUCCESSFUL)

    ratings: RatingInDB = [RatingInDB(**rating) for rating in test_mongo_client.db[ColEnum.RATINGS].find({"song_id": song.id})]
    assert len(ratings) >= 1


@pytest.mark.parametrize("rating,error", [
    (0, "ensure this value is greater than or equal to 1"),
    (-1, "ensure this value is greater than or equal to 1"),
    (6, "ensure this value is less than or equal to 5"),
    (100, "ensure this value is less than or equal to 5"),
])
def test_add_song_rating_fails_with_incorrect_rating_value(
    test_mongo_client: MongoClientWithDB,
    rating: int,
    error: str,
):
    song: SongInDB = SongInDB(**test_mongo_client.db[ColEnum.SONGS].find_one())
    
    with pytest.raises(ValidationError) as validation_error:
        asyncio.new_event_loop().run_until_complete(
            add_song_rating(
                song_id=str(song.id),
                rating=rating,
                mongo_client=test_mongo_client,
            )
        )

    assert len(validation_error.value.errors()) == 1
    assert validation_error.value.errors()[0].get("msg") == error



@pytest.mark.parametrize("ratings,low,average,high", 
    [
        ([1,2,3],1,2,3),
        ([1],1,1,1),
        ([],0,0,0),
        ([1,5],1,3,5),
        ([1,5,5],1,3.66,5),
    ]
)
def test_get_song_rating(
    test_mongo_client: MongoClientWithDB,
    ratings: list[int],
    low: int,
    average: float,
    high: int
):
    song: SongInDB = SongInDB(**test_mongo_client.db[ColEnum.SONGS].find_one())
    col = ColEnum.RATINGS
    if len(list(test_mongo_client.db[col].find({"song_id": song.id}))):
        test_mongo_client.db[col].delete_many({"song_id": song.id})

    if ratings:
        test_mongo_client.db[col].insert_many(
            [
                {"song_id": song.id, "rating": rating} for rating in ratings
            ]
        )

    result: RatingGet = asyncio.new_event_loop().run_until_complete(
        get_song_rating(
            song_id=str(song.id),
            mongo_client=test_mongo_client,
        )
    )

    assert result.lowest_rating == low
    assert result.average_rating == pytest.approx(average, 0.01)
    assert result.highest_rating == high


def test_add_song_rating_fail_when_song_does_not_exist(
    test_mongo_client: MongoClientWithDB,
):
    non_existent_song_object_id = '61b92e572988bae2e02c4b2b'
    with pytest.raises(HTTPException) as exception:
        asyncio.new_event_loop().run_until_complete(
            add_song_rating(
                song_id=non_existent_song_object_id,
                rating=5,
                mongo_client=test_mongo_client,
            )
        )
    assert exception.value.status_code == 404
    assert exception.value.detail == "Song not found"


def test_get_song_rating_fail_when_song_does_not_exist(
    test_mongo_client: MongoClientWithDB,
):
    non_existent_song_object_id = '61b92e572988bae2e02c4b2b'
    with pytest.raises(HTTPException) as exception:
        asyncio.new_event_loop().run_until_complete(
            get_song_rating(
                song_id=non_existent_song_object_id,
                mongo_client=test_mongo_client,
            )
        )
    assert exception.value.status_code == 404
    assert exception.value.detail == "Song not found"
