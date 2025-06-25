from pathlib import Path
import environ
import os
import pytz
from datetime import datetime
from logging import Formatter
from corsheaders.defaults import default_headers

# Load environment variables from .env file
env = environ.Env(
    DEBUG=(bool, True)
)
BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Security settings
SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])

# Installed apps
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    "django_cleanup.apps.CleanupConfig",
]

# Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    'corsheaders.middleware.CorsMiddleware',
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
]

# CORS settings
CORS_ALLOW_METHODS = ['*']
CORS_ALLOW_HEADERS = ['*']
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = False

# URL configuration
ROOT_URLCONF = 'tbilling.urls'

# Templates configuration
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "templates")],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # "modules.context_processors.permissions_processor",

            ],
        },
    },
]

# WSGI application
WSGI_APPLICATION = 'tbilling.wsgi.application'

DATABASES = {  
    'default': {  
        'ENGINE': env("DATABASE_ENGINE", default="django.db.backends.sqlite3"),  
        'NAME': env("DATABASE_NAME", default="billing"),  
        'USER': env("DATABASE_USER", default="postgres"),  
        'PASSWORD': env("DATABASE_PASSWORD", default="mehedi123"),  
        'HOST': env("DATABASE_HOST", default="localhost"),  
        'PORT': env("DATABASE_PORT", default="5432"),  
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Custom User Model
# AUTH_USER_MODEL = 'modules.CustomUser'
LOGIN_URL = '/login/'
LOGOUT_REDIRECT_URL = '/login/'

# Time Zone and Internationalization
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = "/static/"

# Media files (Images, Videos)
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = "/media/"



# Django REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# AWS configuration
AWS_ACCOUNT_ID = env('AWS_ACCOUNT_ID')
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
BUCKET_NAME = env('BUCKET_NAME')
BUCKET_PREFIX = env('BUCKET_PREFIX')
BUCKET_REGION = env('BUCKET_REGION')

# SHA256
SHA256_KEY = env('SHA256_KEY')


# Django Jazzmin settings
# JAZZMIN_SETTINGS = {
#     "site_title": "Ticon AWS Billing",  # Title of the site in the browser tab
#     "site_header": "Billing Admin Panel",  # Header displayed at the top of the admin panel
#     "site_brand": "Ticon AWS Billing",  # Brand name in the header (logo text)
#     "welcome_sign": "Welcome to the Ticon AWS Billing Admin Panel",  # Welcome message
#     "copyright": "Ticon System Limited © 2025",  # Copyright information
#     "show_sidebar": True,  # Show/hide sidebar for easy navigation
#     # "show_ui_builder": True,  # Allows you to build custom UI components easily
#     "theme": "dark",  # Customizable theme; you can create or use an existing one
#     "search_model": [
#         "modules.CustomUser",  # Enable search for these models in the admin
#         # "modules.BillingRecord",  # Example of another model you may want to search
#     ],
#     "topmenu_links": [
#         {"name": "Dashboard", "url": "admin:index", "permissions": ["auth.view_user"]},  # Admin dashboard link
#         {"name": "Billing Reports", "url": "/billing-reports", "new_window": True},  # Add a custom link for reports
#     ],
#     # "user_avatar": "path/to/default/avatar.png",  # Set default avatar image for users
#     "changeform_format": "vertical",  # Choose between horizontal or vertical layout for change forms
#     "default_related_widget": "Select2",  # Use Select2 widget for better related model field selection
#     "navigation_expanded": True,  # Automatically expand sidebar navigation
#     "hide_apps": ["auth"],  # Hide certain apps from the sidebar if not needed
#     "hide_models": ["auth.Group", "auth.Permission"],  # Hide unnecessary models in the admin panel
#     "icons": {
#         "auth.User": "fas fa-user",  # Custom icons for specific models
#         # "modules.BillingRecord": "fas fa-credit-card",  # Example icon for your custom model
#     },
#     # "custom_css": "path/to/your/custom/styles.css",  # Add custom CSS file for advanced styling
#     # "custom_js": "path/to/your/custom/script.js",  # Add custom JavaScript for enhanced interactivity
#     "site_logo": 'images/ticon.png',  # Add the path to your logo image
    
# }

JAZZMIN_UI_TWEAKS = {
    "theme": "darkly",
    "navbar": "navbar-dark",
}

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 1 week

DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(BASE_DIR, 'django_cache'),  # or '/tmp/django_cache'
    }
}