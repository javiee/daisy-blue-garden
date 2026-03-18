from .base import *  # noqa
import environ

env = environ.Env()

DEBUG = False
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])
