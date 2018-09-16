# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/
import os

import dj_database_url

from fixdin.settings.base import *

SECRET_KEY = os.environ['SECRET_KEY']
DEBUG = False

# Databases
DATABASES['default'] = dj_database_url.config()

AWS_STORAGE_BUCKET_NAME = os.environ['AWS_STORAGE_BUCKET_NAME']

# Allow all host headers
ALLOWED_HOSTS = ['*']

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

#ADMINS = (('Guilherme Latrova','guilhermelatrova@hotmail.com'),)
