# -*- coding: utf-8 -*-

from __future__ import unicode_literals
"""
Django settings for availability_api.

Environmental variables triggered in project's env_avl/bin/activate, when using runserver,
  or env_avl/bin/activate_this.py, when using apache via passenger.
"""

import json, logging, os


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['AVL_API__SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = json.loads( os.environ['AVL_API__DEBUG_JSON'] )  # will be True or False

ADMINS = json.loads( os.environ['AVL_API__ADMINS_JSON'] )
MANAGERS = ADMINS

ALLOWED_HOSTS = json.loads( os.environ['AVL_API__ALLOWED_HOSTS'] )  # list


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'availability_app',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'config.urls'

WSGI_APPLICATION = 'config.passenger_wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = json.loads( os.environ['AVL_API__DATABASES_JSON'] )


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/New_York'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = os.environ['AVL_API__STATIC_URL']
STATIC_ROOT = os.environ['AVL_API__STATIC_ROOT']  # needed for collectstatic command


# Templates

templt_dirs = json.loads( os.environ['AVL_API__TEMPLATE_DIRS'] )  # list
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': templt_dirs,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        # 'TEMPLATE_DEBUG': DEBUG
        },
    },
]


# Email
EMAIL_HOST = os.environ['AVL_API__EMAIL_HOST']
EMAIL_PORT = int( os.environ['AVL_API__EMAIL_PORT'] )


# sessions

# <https://docs.djangoproject.com/en/1.9/ref/settings/#std:setting-SESSION_SAVE_EVERY_REQUEST>
# Thinking: not that many concurrent users, and no pages where session info isn't required, so overhead is reasonable.
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# logging

## disable module loggers
# existing_logger_names = logging.getLogger().manager.loggerDict.keys()
# print '- EXISTING_LOGGER_NAMES, `%s`' % existing_logger_names
logging.getLogger('requests').setLevel( logging.WARNING )

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': "[%(asctime)s] %(levelname)s [%(module)s-%(funcName)s()::%(lineno)d] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
        'microseconds': {
            # 'format': "[%(asctime)s] %(levelname)s [%(module)s-%(funcName)s()::%(lineno)d] %(message)s",
            # 'format': "[%(asctime)s.%(msecs)03d[%(levelname)-8s]:%(created).6f %(message)s",
            # 'format': "[%(asctime)s.%(msecs)03d] -- %(levelname)s -- %(created).6f",
            # 'format': "[%(asctime)s--%(created).6f--] %(levelname)s [%(module)s-%(funcName)s()::%(lineno)d] %(message)s",
            'format': "%(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        }
    },
    'handlers': {
        'logfile': {
            'level':'DEBUG',
            'class':'logging.FileHandler',  # note: configure server to use system's log-rotate to avoid permissions issues
            'filename': os.environ.get('AVL_API__LOG_PATH'),
            'formatter': 'standard',
        },
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'standard'
        },
        'stats_logfile': {
            'level':'DEBUG',
            'class':'logging.FileHandler',  # note: configure server to use system's log-rotate to avoid permissions issues
            'filename': os.environ.get( 'AVL_API__STATS_LOG_PATH' ),
            'formatter': 'microseconds',
        },
    },
    'loggers': {
        'availability_app': {
            'handlers': ['logfile'],
            'level': os.environ.get( 'AVL_API__LOG_LEVEL' ),
            'propagate': False,
        },
        'stats_logger': {
            'handlers': ['stats_logfile'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': True,
#     'formatters': {
#         'standard': {
#             'format': "[%(asctime)s] %(levelname)s [%(module)s-%(funcName)s()::%(lineno)d] %(message)s",
#             'datefmt' : "%d/%b/%Y %H:%M:%S"
#         }
#     },
#     'handlers': {
#         'logfile': {
#             'level':'DEBUG',
#             'class':'logging.FileHandler',  # note: configure server to use system's log-rotate to avoid permissions issues
#             'filename': os.environ.get('AVL_API__LOG_PATH'),
#             'formatter': 'standard',
#         },
#         'console':{
#             'level':'DEBUG',
#             'class':'logging.StreamHandler',
#             'formatter': 'standard'
#         },
#     },
#     'loggers': {
#         'availability_app': {
#             'handlers': ['logfile'],
#             'level': os.environ.get('AVL_API__LOG_LEVEL'),
#         },
#     }
# }

## https://docs.djangoproject.com/en/1.11/topics/cache/
CACHES = json.loads( os.environ['AVL_API__CACHES_JSON'] )
