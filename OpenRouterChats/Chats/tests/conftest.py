import pytest
import os
import django
from django.test import Client
from django.contrib.auth import get_user_model
from django.conf import settings

# Настройка Django для тестов
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OpenRouterChats.settings')
django.setup()

from Chats.models import Users, Teachers


@pytest.fixture(scope='session')
def django_db_setup():
    """Настройка тестовой базы данных"""
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }


@pytest.fixture
def client():
    """Фикстура для тестового клиента Django"""
    return Client()


@pytest.fixture
def active_user():
    """Фикстура для создания активного тестового пользователя"""
    user = Users.objects.create_user(
        login='testuser',
        password='testpass123',
        type='user',
        is_active=True
    )
    return user


@pytest.fixture
def inactive_user():
    """Фикстура для создания неактивного тестового пользователя"""
    user = Users.objects.create_user(
        login='inactiveuser',
        password='testpass123',
        type='user',
        is_active=False
    )
    return user


@pytest.fixture
def admin_user():
    """Фикстура для создания администратора"""
    user = Users.objects.create_user(
        login='adminuser',
        password='adminpass123',
        type='admin',
        is_active=True
    )
    return user


@pytest.fixture
def test_teacher(active_user):
    """Фикстура для создания тестового преподавателя"""
    teacher = Teachers.objects.create(
        name='Test Teacher',
        prompt='Test prompt for teacher',
        user=active_user
    )
    return teacher


@pytest.fixture
def teacher_without_user():
    """Фикстура для создания преподавателя без привязки к пользователю"""
    teacher = Teachers.objects.create(
        name='Independent Teacher',
        prompt='Independent teacher prompt'
    )
    return teacher


@pytest.fixture
def authenticated_client(client, active_user):
    """Фикстура для авторизованного клиента"""
    client.login(login=active_user.login, password='testpass123')
    return client


@pytest.fixture
def authenticated_admin_client(client, admin_user):
    """Фикстура для авторизованного клиента-администратора"""
    client.login(login=admin_user.login, password='adminpass123')
    return client


@pytest.fixture
def multiple_users():
    """Фикстура для создания нескольких пользователей"""
    users = []
    for i in range(3):
        user = Users.objects.create_user(
            login=f'user{i}',
            password=f'pass{i}',
            type='user',
            is_active=True
        )
        users.append(user)
    return users


@pytest.fixture
def multiple_teachers(active_user):
    """Фикстура для создания нескольких преподавателей"""
    teachers = []
    for i in range(3):
        teacher = Teachers.objects.create(
            name=f'Teacher {i}',
            prompt=f'Prompt for teacher {i}',
            user=active_user if i % 2 == 0 else None
        )
        teachers.append(teacher)
    return teachers
