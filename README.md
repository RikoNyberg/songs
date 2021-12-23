# Songs application 
This is an API that lists songs and lets you review them.


# Setting up
Run the following command in this folder:
```
docker run --detach --name songs_db --publish 127.0.0.1:27017:27017 mongo:4.4
pip install -r requirements.txt
```
Ps. You need [Docker](https://www.docker.com/get-started) for this and I suggest using some virtual environment

# Run locally and test manually
```
python3 init_db.py
uvicorn router:app --reload
```
Then test the API manually from:
## http://127.0.0.1:8000/docs

# Run all tests
```
pytest
```