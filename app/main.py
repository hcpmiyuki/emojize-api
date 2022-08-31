from fastapi import FastAPI
from utils.tweet_emojizer import Emojize
from dotenv import load_dotenv
load_dotenv()
app = FastAPI()
emojizer = Emojize()

@app.get('/emojize')
async def emojize(tweet: str, emoji_level:int = 3):
    tweet_emojized = emojizer(tweet, emoji_level)
    
    return {'result': tweet_emojized}

@app.get('/')
async def hello():
    return {'msg': 'hello world!'}
