from .settings import *

DEBUG = False
ALLOWED_HOSTS = ['*']


# Production database configuration would go here
# Static files configuration for production
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

