from fixdin.settings.base import *

DEBUG = True

SECRET_KEY = 'ji$1&jbw!u2d)6a&^zj#8&#gu1%eg$31y#&)@#y2%5h9vlwl^%'

ALLOWED_HOSTS = ['*'] 
 
CORS_ORIGIN_ALLOW_ALL = True 

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'fixdin',
        'USER': 'postgres',
        'PASSWORD': '1',
        'HOST': 'localhost',
        'PORT': '5432'
    }
}
