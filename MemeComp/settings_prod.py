import os
import dotenv
dotenv.load_dotenv('.env.prod')

SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = False
WEBSOCKET_SCHEME = 'wss'
ALLOWED_HOSTS = ['127.0.0.1', '0.0.0.0', "meme-competition.fly.dev"]
CSRF_TRUSTED_ORIGINS = ["https://meme-competition.fly.dev"]
CSRF_ALLOWED_ORIGINS = ["https://meme-competition.fly.dev"]
CORS_ORIGINS_WHITELIST = ["https://meme-competition.fly.dev"]
