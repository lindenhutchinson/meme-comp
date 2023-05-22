import os
import dotenv
dotenv.load_dotenv('.env.dev')

SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = True
WEBSOCKET_SCHEME = 'ws'
ALLOWED_HOSTS = ['127.0.0.1', '0.0.0.0', "localhost"]
CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1', 'http://0.0.0.0', "http://localhost"]
CSRF_ALLOWED_ORIGINS = ['http://127.0.0.1', 'http://0.0.0.0', "http://localhost"]
CORS_ORIGINS_WHITELIST = ['http://127.0.0.1', 'http://0.0.0.0', "http://localhost"]