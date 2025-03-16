from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-2mwt(&bft$#=x60=z8r%$y4#g@$zm_gjooi*k2l@(f%(#k6lqi"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'drive',
        'USER': 'postgres',
        'PASSWORD': 'root',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# MinIO settings
AWS_S3_ENDPOINT_URL = "http://localhost:9000"
AWS_ACCESS_KEY_ID = "admin"
AWS_SECRET_ACCESS_KEY = "admin123"
AWS_STORAGE_BUCKET_NAME = "mybucket"
AWS_S3_ADDRESSING_STYLE = "path"
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage" 