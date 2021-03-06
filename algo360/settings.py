"""
Django settings for algo360 project.

Generated by 'django-admin startproject' using Django 1.10.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os, socket, configparser

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

common = configparser.SafeConfigParser(allow_no_value=True)
config = configparser.SafeConfigParser(allow_no_value=True)
        
common.read('%s/configs/common.conf' % (BASE_DIR))

if socket.gethostname().startswith('DIVY'):
    DJANGO_HOST = "testing"
    config.read('%s/configs/testing.conf' % (BASE_DIR))
elif socket.gethostname().startswith('ip-172-31-29-171') or socket.gethostname().startswith('ip-172-31-19-248') or socket.gethostname().startswith('ip-172-31-'):     #ebs OR mumbai
    DJANGO_HOST = "production"
    config.read('%s/configs/production.conf' % (BASE_DIR))
else:
    DJANGO_HOST = "testing"
    config.read('%s/configs/testing.conf' % (BASE_DIR))
    
SECRET_KEY = config.get('security', 'SECRET_KEY')

DEBUG = config.getboolean('general', 'DEBUG')

ADMINS = (('Webmaster',common.get('admins', 'Webmaster')),('Administrator',common.get('admins', 'Administrator')))

MANAGERS = ADMINS

ALLOWED_HOSTS = config.get('lists', 'ALLOWED_HOSTS').split(', ')

INSTALLED_APPS = config.get('lists', 'INSTALLED_APPS').split(', ')

AUTHENTICATION_BACKENDS = tuple(config.get('lists', 'AUTHENTICATION_BACKENDS').split(', '))

MIDDLEWARE = config.get('lists', 'MIDDLEWARE').split(', ')
    
if DJANGO_HOST == "testing":

    #INTERNAL_IPS = ['localhost', '127.0.0.1',]
    
    DEBUG_TOOLBAR_PANELS = config.get('lists', 'DEBUG_TOOLBAR_PANELS').split(', ')

    CONFIG_DEFAULTS = {
        'RESULTS_CACHE_SIZE': 3,
        'SHOW_COLLAPSED': True,
        'SQL_WARNING_THRESHOLD': 50,   # milliseconds
    }
    
elif DJANGO_HOST == "production":

    CORS_ORIGIN_ALLOW_ALL = config.getboolean('CORS', 'CORS_ORIGIN_ALLOW_ALL')
    
    #Abhishek added

    #SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    #SESSION_COOKIE_SECURE = True
    #CSRF_COOKIE_SECURE = True

    #SECURE_SSL_REDIRECT = True
    #os.environ['wsgi.url_scheme'] = 'https'

    CACHES = {
        'default': {
            'BACKEND': config.get('CACHES', 'BACKEND'),
            'LOCATION': config.get('CACHES', 'LOCATION'),
            'TIMEOUT': config.getint('CACHES', 'TIMEOUT'),
            'OPTIONS': {
                'MAX_ENTRIES': config.getint('CACHES', 'MAX_ENTRIES')
            }
        }
    }

    CACHE_MIDDLEWARE_SECONDS = config.getint('CACHES', 'CACHE_MIDDLEWARE_SECONDS')  #for 'max-age' header, set by UpdateCacheMiddleware
    
    pass

DATABASES = {
    common.get('database_default', 'ALIAS'): {
        'ENGINE': common.get('database_default', 'ENGINE'),
        'NAME': os.path.join(BASE_DIR, common.get('database_default', 'NAME')),
        'USER': common.get('database_default', 'USER'),
        'PASSWORD': common.get('database_default', 'PASSWORD'),
    },
}

LOGIN_URL = common.get('general', 'LOGIN_URL')

LOGIN_REDIRECT_URL = '/'

GEOIP_PATH = os.path.join(BASE_DIR, common.get('general', 'GEOIP_PATH'))

#APPEND_SLASH = True

ROOT_URLCONF = common.get('general', 'ROOT_URLCONF')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'main/')],   # ADDED SEPERATELY
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

WSGI_APPLICATION = common.get('general', 'WSGI_APPLICATION')

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

LANGUAGE_CODE = common.get('general', 'LANGUAGE_CODE')

TIME_ZONE = common.get('general', 'TIME_ZONE')

USE_I18N = True

USE_L10N = True

USE_TZ = common.getboolean('general', 'USE_TZ')

STATIC_URL = common.get('static', 'STATIC_URL')

STATIC_ROOT = os.path.join(BASE_DIR, common.get('static', 'STATIC_ROOT'))

STATIC_PATH = os.path.join(BASE_DIR, common.get('static', 'STATIC_PATH'))

STATICFILES_DIRS = (
    STATIC_PATH,
)

OAUTH2_PROVIDER = {
    'SCOPES': {
        'read': 'Read scope',
    },
    'ACCESS_TOKEN_EXPIRE_SECONDS': common.getint('expiration', 'ACCESS_TOKEN'),
    'AUTHORIZATION_CODE_EXPIRE_SECONDS': common.getint('expiration', 'AUTHORIZATION_CODE'),
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.ext.rest_framework.OAuth2Authentication',
        'oauth2_provider.ext.rest_framework.TokenHasScope',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100
}

EMAIL_USE_TLS = common.get('email', 'USE_TLS') 
EMAIL_HOST = common.get('email', 'HOST')
EMAIL_HOST_USER = common.get('email', 'HOST_USER')
EMAIL_HOST_PASSWORD = common.get('email', 'HOST_PASSWORD') 
EMAIL_PORT = common.getint('email', 'PORT') 

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler'
        }
    },
    'loggers': {
        'django.security.DisallowedHost': {
            'handlers': ['null'],
            'propagate': False,
        }
    }
}
