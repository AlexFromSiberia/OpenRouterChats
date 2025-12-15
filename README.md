
# Что нужно сделать руками (миграции + первый пользователь)
Запусти команды из папки, где лежит manage.py: OpenRouterChats

# Миграции

```bash
python manage.py makemigrations
python manage.py migrate
```

# Создать первого пользователя (чтобы пароль корректно захэшировался)

```bash
python manage.py shell
```
Внутри shell:

```python
from Chats.models import Users
u = Users(login="admin")
u.set_password("admin123")
u.save()
```

# Create an admin user (superuser)
In another terminal (same folder with manage.py):
```bash
python manage.py createsuperuser
```

# Запуск

```bash
python manage.py runserver
```
Открываешь http://127.0.0.1:8000/login/
После входа попадёшь на http://127.0.0.1:8000/ и увидишь приветствие.





# Нового пользователя нужно активировать в админке