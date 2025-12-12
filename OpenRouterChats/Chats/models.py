from django.db import models
from django.contrib.auth.hashers import check_password, make_password

# Create your models here.


class Users(models.Model):
    """Пользователи и хэши паролей
    """
    login = models.CharField(max_length=150, unique=True)
    password_hash = models.CharField(max_length=128)

    class Meta:
        db_table = 'Users'

    def __str__(self):
        return self.login

    def set_password(self, raw_password: str) -> None:
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password(raw_password, self.password_hash)
