import os

if os.getenv('ENVIRONMENT') == 'production':
    from .settings_prod import *
else:
    from .settings_dev import *