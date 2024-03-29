import os
import dotenv

dotenv.load_dotenv(".env.dev")

SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = True
WEBSOCKET_SCHEME = "ws"
ALLOWED_HOSTS = ["127.0.0.1", "0.0.0.0", "localhost", "192.168.1.2"]
CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1",
    "http://0.0.0.0",
    "http://localhost",
    "http://192.168.1.2",
]
CSRF_ALLOWED_ORIGINS = [
    "http://127.0.0.1",
    "http://0.0.0.0",
    "http://localhost",
    "http://192.168.1.2",
]
CORS_ORIGINS_WHITELIST = [
    "http://127.0.0.1",
    "http://0.0.0.0",
    "http://localhost",
    "http://192.168.1.2",
]

REDIS_URL = CELERY_BROKER_URL = "redis://localhost:6379"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [{"address": REDIS_URL}]},
    }
}
