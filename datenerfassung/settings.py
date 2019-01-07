# -*- coding: utf-8 -*-

"""
Django settings for datenerfassung project.

Generated by 'django-admin startproject' using Django 1.9.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/


# Application definition

DATENMANAGEMENT_VERSION = '1.4.1'

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
]

LOCAL_APPS = [
    'datenmanagement',
]

THIRD_PARTY_APPS = [
    'datetimewidget',
    'guardian',
    'leaflet',
    'requests',
    'rest_framework',
    'multiselectfield',
    'django_user_agents',
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS + THIRD_PARTY_APPS

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django_user_agents.middleware.UserAgentMiddleware',
]

ROOT_URLCONF = 'datenerfassung.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'datenerfassung.context_processors.datenmanagement_version',
                'datenerfassung.context_processors.django_version',
                'datenerfassung.context_processors.address_search_key',
                'datenerfassung.context_processors.include_login_form',
            ],
            'libraries': {
                'datenmanagement_tags': 'datenmanagement.tags.tags'
            },
        },
    },
]

WSGI_APPLICATION = 'datenerfassung.wsgi.application'

READONLY_FIELD_DEFAULT = '00000000'


# Guardian

ANONYMOUS_USER_ID = -1


# Leaflet

LEAFLET_CONFIG = {
    'SPATIAL_EXTENT': (10.53001,52.98541,14.68873,54.82175),
    'DEFAULT_CENTER': (54.14775,12.14945),
    'DEFAULT_ZOOM': 11,
    'MIN_ZOOM': 11,
    'MAX_ZOOM': 18,
    'TILES': [],
    'SRID': 3857,
    'ATTRIBUTION_PREFIX': '',
    'RESET_VIEW': False,
    'PLUGINS': {
        'forms': {
            'auto_include': True
        }
    }
}


# REST framework

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAdminUser',
    ],
    'DATETIME_FORMAT': 'iso-8601',
    'DATE_FORMAT': 'iso-8601',
    'TIME_FORMAT': 'iso-8601',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
}


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'de-de'

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/datenerfassung_static/'

STATIC_ROOT = '/usr/local/django_datenerfassung/datenerfassung/static'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'assets/'),
)


# Link auf Konfigurationsdatei mit weiteren Parametern,
# die nicht unter Git-Versionskontrolle fallen sollen (Secret keys etc.)

try:
    from datenerfassung.secrets import *
except ImportError:
    pass
