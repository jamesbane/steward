"""
Django settings for steward project.

Generated by 'django-admin startproject' using Django 1.9.1.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os
import json
import ldap
import string
import random
import logging

from django_auth_ldap.config import LDAPSearch, GroupOfNamesType



BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_FILE = os.path.abspath(os.path.join(BASE_DIR, "settings.json"))
if os.path.isfile(SETTINGS_FILE):
    with open(SETTINGS_FILE) as f:
        env = json.loads(f.read())
else:
    raise Exception('Could not open settings.json')


# =====================================
# Core settings
# =====================================
if 'secret_key' in env['django']:
    SECRET_KEY = env['django']['secret_key']
else:
    SECRET_KEY = ''.join([random.SystemRandom().choice("{}{}{}".format(string.ascii_letters, string.digits, string.punctuation)) for i in range(50)])
    env['django']['secret_key'] = SECRET_KEY
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(env, f, sort_keys=True, indent=4)
DEBUG = env['django']['debug']
ALLOWED_HOSTS = env['django']['allowed_hosts']


# =====================================
# Application definition
# =====================================
INSTALLED_APPS = [
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',

    # Project
    'steward',
    'tools',

    # Third Party
    'django_rq',
]
MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'steward.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['{}/templates'.format(BASE_DIR)],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
WSGI_APPLICATION = 'steward.wsgi.application'


# =====================================
# Authentication
# =====================================
AUTHENTICATION_BACKENDS = [
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
]
AUTH_LDAP_SERVER_URI = "ldap://ds01.ipa.cspirevoice.com"
AUTH_LDAP_BIND_DN = "uid=steward,cn=sysaccounts,cn=etc,dc=ipa,dc=cspirevoice,dc=com"
AUTH_LDAP_BIND_PASSWORD = "najica123"
AUTH_LDAP_GROUP_TYPE = GroupOfNamesType(name_attr="cn")
AUTH_LDAP_GROUP_SEARCH = LDAPSearch("cn=groups,cn=accounts,dc=ipa,dc=cspirevoice,dc=com",
    ldap.SCOPE_SUBTREE, "(objectClass=groupOfNames)"
)
AUTH_LDAP_USER_DN_TEMPLATE = "uid=%(user)s,cn=users,cn=accounts,dc=ipa,dc=cspirevoice,dc=com"
AUTH_LDAP_USER_ATTR_MAP = {"first_name": "givenName", "last_name": "sn", "email": "mail"}
AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    "is_active": "cn=admins,cn=groups,cn=accounts,dc=ipa,dc=cspirevoice,dc=com",
    "is_staff": "cn=admins,cn=groups,cn=accounts,dc=ipa,dc=cspirevoice,dc=com",
    "is_superuser": "cn=admins,cn=groups,cn=accounts,dc=ipa,dc=cspirevoice,dc=com",
}

# logger = logging.getLogger('django_auth_ldap')
# logger.addHandler(logging.StreamHandler())
# logger.setLevel(logging.DEBUG)


# =====================================
# Database
# =====================================
DATABASES = {
    'default': {
        'ENGINE': env['database']['engine'],
        'NAME': env['database']['db_name'],
        'USER': env['database']['username'],
        'PASSWORD': env['database']['password'],
        'HOST': env['database']['host'],
        'PORT': env['database']['port'],
    }
}


# =====================================
# Password validation
# =====================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# =====================================
# Where to redirect after login (and no next reference)
# =====================================
LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "/accounts/login/"
LOGOUT_URL = "/accounts/logout/"


# =====================================
# Internationalization
# =====================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# =====================================
# Static files (CSS, JavaScript, Images)
# =====================================
STATIC_URL = '/static/'
STATIC_ROOT = '{}/static/'.format(BASE_DIR)


# =====================================
# Redis Queue
# =====================================
RQ_QUEUES = {
    'default': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0,
    },
}


# =====================================
# Email
# =====================================
EMAIL_HOST = env['email']['smtp_server']
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
DEFAULT_FROM_EMAIL = env['email']['from_address']
SERVER_EMAIL = env['email']['from_address']


# =====================================
# Admins & Managers
# =====================================
ADMINS = env['admins']
MANAGERS = ADMINS
