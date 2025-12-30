from django.db import models
from django.contrib.auth.hashers import check_password, make_password


class Users(models.Model):
    """Пользователи
    """
    
    TYPES = [
        ('user', 'Пользователь'),
        ('admin', 'Администратор'),
    ]
    
    login = models.CharField(max_length=150, unique=True)
    password_hash = models.CharField(max_length=128)
    type = models.CharField(max_length=50, choices=TYPES, default='user')
    # По умолчанию False - всех новых пользователей должен активировать администратор
    is_active = models.BooleanField(default=False)

    class Meta:
        db_table = 'Users'

    def __str__(self) -> str:
        return self.login

    def set_password(self, raw_password: str) -> None:
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password(raw_password, self.password_hash)


class Teachers(models.Model):
    """Преподаватели
    """
    name = models.CharField(max_length=200)
    prompt = models.TextField(null=True, blank=True, max_length=10000)
    user = models.ForeignKey('Users', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'Teachers'

    def __str__(self) -> str:
        return self.name
    