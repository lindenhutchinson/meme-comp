import os
import dotenv
from urllib.parse import urlparse
import sentry_sdk

dotenv.load_dotenv(".env.prod")
SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = False
WEBSOCKET_SCHEME = "wss"
ALLOWED_HOSTS = ["127.0.0.1", "0.0.0.0", "meme-competition.fly.dev"]
CSRF_TRUSTED_ORIGINS = ["https://meme-competition.fly.dev"]
CSRF_ALLOWED_ORIGINS = ["https://meme-competition.fly.dev"]
CORS_ORIGINS_WHITELIST = ["https://meme-competition.fly.dev"]


# code from https://stackoverflow.com/questions/62777377/long-url-including-a-key-causes-unicode-idna-codec-decoding-error-whilst-using
def parse_redis_url(url):
    """parses a redis url into component parts, stripping password from the host.
    Long keys in the url result in parsing errors, since labels within a hostname cannot exceed 64 characters under
    idna rules.
    In that event, we remove the key/password so that it can be passed separately to the RedisChannelLayer.
    Heroku REDIS_URL does not include the DB number, so we allow for a default value of '0'
    """
    parsed = urlparse(url)
    parts = parsed.netloc.split(":")
    host = ":".join(parts[0:-1])
    port = parts[-1]
    path = parsed.path.split("/")[1:]
    db = int(path[0]) if len(path) >= 1 else 0

    user, password = (None, None)
    if "@" in host:
        creds, host = host.split("@")
        user, password = creds.split(":")
        host = f"{user}@{host}"

    return host, port, user, password, db


REDIS_URL = os.environ.get("REDIS", default="redis://localhost:6379")
REDIS_HOST, REDIS_PORT, REDIS_USER, REDIS_PASSWORD, REDIS_DB = parse_redis_url(
    REDIS_URL
)


CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [
                {
                    "address": f"redis://{REDIS_HOST}:{REDIS_PORT}",
                    "db": REDIS_DB,
                    "password": REDIS_PASSWORD,
                }
            ],
        },
    },
}


sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    enable_tracing=True,
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=0.5,
)
