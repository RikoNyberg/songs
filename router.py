from fastapi.exceptions import HTTPException
from bson.objectid import ObjectId
from fastapi.params import Depends
from pydantic.types import conint
from app.schemas.rating import (
    RatingGet,
    RatingPostConfirmation,
    RatingPostConfirmationResultEnum,
)
from db.get_db import ColEnum, MongoClientWithDB, get_db
from typing import List, Optional
from app.schemas.song import SongGet, SongsAverageDifficultyGet
from app.schemas.rating import RatingValidator
from db.schemas.rating import RatingInDB
from db.schemas.song import SongInDB
from fastapi import FastAPI

app: FastAPI = FastAPI()


@app.get("/songs", response_model=List[SongGet])
async def get_songs(
    offset: int = 0,
    limit: int = 200,
    message: Optional[str] = None,
    mongo_client: MongoClientWithDB = Depends(get_db)
    # NOTE: Using last_id as a skip criteria in
    #       big datasets would make pagination faster:
    # last_id: Optional[str] = None,
) -> List[SongGet]:
    if message:
        return [
            SongGet(**song, id=str(song["_id"]))
            for song in mongo_client.db[ColEnum.SONGS]
            .find(
                {
                    "$or": [
                        {"artist": {"$regex": message, "$options": "i"}},
                        {"title": {"$regex": message, "$options": "i"}},
                    ]
                }
            )
            .skip(offset)
            .limit(limit)
            # NOTE: Using text index search (already created) is much faster but
            #       the default Tokenization includes only complete words:
            # for song in mongo_client.db[ColEnum.SONGS].find({"$text": {"$search": message}}).skip(offset).limit(limit)
        ]
    else:
        return [
            SongGet(**song, id=str(song["_id"]))
            for song in mongo_client.db[ColEnum.SONGS].find().skip(offset).limit(limit)
        ]


@app.get("/songs/average_difficulty", response_model=SongsAverageDifficultyGet)
async def get_songs_average_difficulty(
    level: Optional[conint(gt=0, le=100)] = None,
    mongo_client: MongoClientWithDB = Depends(get_db),
) -> SongsAverageDifficultyGet:
    songs = [
        SongInDB(**song)
        for song in mongo_client.db[ColEnum.SONGS].find(
            {"level": level} if level else {}
        )
    ]
    return SongsAverageDifficultyGet(
        average_difficulty=sum([song.difficulty for song in songs]) / len(songs)
        if len(songs)
        else 0
    )


@app.post("/songs/{song_id}/ratings", response_model=RatingPostConfirmation)
async def add_song_rating(
    song_id: str,
    rating: conint(ge=1, le=5),
    mongo_client: MongoClientWithDB = Depends(get_db),
) -> RatingPostConfirmation:
    RatingValidator(rating=rating)
    if not mongo_client.db[ColEnum.SONGS].find_one({"_id": ObjectId(song_id)}):
        raise HTTPException(status_code=404, detail="Song not found")

    mongo_client.db[ColEnum.RATINGS].insert_one(
        {"song_id": ObjectId(song_id), "rating": rating}
    )

    return RatingPostConfirmation(result=RatingPostConfirmationResultEnum.SUCCESSFUL)


@app.get("/songs/{song_id}/ratings", response_model=RatingGet)
async def get_song_rating(
    song_id: str, mongo_client: MongoClientWithDB = Depends(get_db)
) -> RatingGet:
    if not mongo_client.db[ColEnum.SONGS].find_one({"_id": ObjectId(song_id)}):
        raise HTTPException(status_code=404, detail="Song not found")

    ratings = [
        RatingInDB(**rating_in_db).rating
        for rating_in_db in mongo_client.db[ColEnum.RATINGS].find(
            {"song_id": ObjectId(song_id)}
        )
    ]
    if not ratings:
        return RatingGet(average_rating=0, lowest_rating=0, highest_rating=0)
        # NOTE: Could also raise a HTTPException... depending what are the requirements
        # raise HTTPException(status_code=404, detail="No ratings found for the song")

    return RatingGet(
        average_rating=sum(ratings) / len(ratings),
        lowest_rating=min(ratings),
        highest_rating=max(ratings),
    )
