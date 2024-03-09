# Create your models here.

from django.contrib.auth.models import AbstractUser
from oauth2_provider.models import AbstractApplication


class User(AbstractUser):
    pass

