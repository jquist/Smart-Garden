from django.contrib import messages
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent

# Security settings which would need correcting for production
DEBUG = True
ALLOWED_HOSTS = ['*']
CORS_ORIGIN_ALLOW_ALL = DEBUG
CORS_ALLOW_ALL_ORIGINS = True
SECRET_KEY = 'django-insecure-session-key'

# For our React SPA, we will explicitly allow unauthenticated users
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny']}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'data_wizard',
    'data_wizard.sources',
    'crispy_forms',
    'crispy_bootstrap5',
    'Plant_plotter',
    'corsheaders'
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware'
]

ROOT_URLCONF = 'Plant_plotter_settings.urls'

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
                'django.contrib.messages.context_processors.messages'
            ]
        }
    }
]

WSGI_APPLICATION = 'Plant_plotter_settings.wsgi.application'

# Database for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3'
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Internationalisation
LANGUAGE_CODE = 'en'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
LANGUAGES = [('en', 'English')]

# Locale path
LOCALE_PATHS = [BASE_DIR / 'Plant_plotter' / 'locale']

# Static files
STATIC_ROOT = BASE_DIR / 'static/'
STATIC_URL = 'static/'

# Media for uploaded files
MEDIA_ROOT = BASE_DIR / 'media/'
MEDIA_URL = '/media/'

# Set up for simple Bootstrap theming
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'
MESSAGE_TAGS = {
    messages.DEBUG: 'alert-info',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger'
}

# Account redirects
LOGOUT_REDIRECT_URL = '/'
LOGIN_REDIRECT_URL = '/'
