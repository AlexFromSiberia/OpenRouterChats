import pytest
from django.test import TestCase, Client
from django.contrib import messages
from django.contrib.messages import get_messages
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch, MagicMock
from freezegun import freeze_time

from Chats.models import Users


class TestLoginView(TestCase):
    """Интеграционные тесты для login_view"""

    def setUp(self):
        """Подготовка данных для тестов"""
        self.client = Client()
        self.login_url = reverse('login')
        self.home_url = reverse('home')
        
        # Создаем тестовых пользователей
        self.active_user = Users.objects.create(
            login='activeuser',
            password_hash='hashed_pass',
            is_active=True
        )
        self.active_user.set_password('correctpass')
        self.active_user.save()
        
        self.inactive_user = Users.objects.create(
            login='inactiveuser',
            password_hash='hashed_pass',
            is_active=False
        )
        self.inactive_user.set_password('correctpass')
        self.inactive_user.save()

    def tearDown(self):
        """Очистка после каждого теста"""
        # Очищаем сообщения
        messages_list = list(get_messages(self.client.request))
        # Сбрасываем сессию
        self.client.session.flush()

    def test_login_page_get(self):
        """Тест GET запрос возвращает форму входа"""
        response = self.client.get(self.login_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Chats/login.html')
        self.assertContains(response, 'Вход')
        self.assertContains(response, 'name="login"')
        self.assertContains(response, 'name="password"')

    def test_login_success_active_user(self):
        """Тест успешный вход активного пользователя"""
        response = self.client.post(self.login_url, {
            'login': 'activeuser',
            'password': 'correctpass'
        })
        
        # Проверяем редирект на home
        self.assertRedirects(response, self.home_url)
        
        # Проверяем создание сессии
        self.assertIn('user_id', self.client.session)
        self.assertEqual(self.client.session['user_id'], self.active_user.id)
        self.assertIn('user_login', self.client.session)
        self.assertEqual(self.client.session['user_login'], 'activeuser')

    def test_login_redirect_to_home(self):
        """Тест редирект на home после входа"""
        response = self.client.post(self.login_url, {
            'login': 'activeuser',
            'password': 'correctpass'
        }, follow=True)
        
        self.assertRedirects(response, self.home_url)
        # Проверяем что мы действительно на home странице
        self.assertTemplateUsed(response, 'Chats/home.html')

    @patch('Chats.views.sleep')
    def test_login_inactive_user(self, mock_sleep):
        """Тест неактивный пользователь не может войти"""
        response = self.client.post(self.login_url, {
            'login': 'inactiveuser',
            'password': 'correctpass'
        })
        
        # Проверяем что остаемся на странице логина
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Chats/login.html')
        
        # Проверяем что сессия не создана
        self.assertNotIn('user_id', self.client.session)
        self.assertNotIn('user_login', self.client.session)
        
        # Проверяем сообщение
        messages_list = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), 'Логин и пароль верные, дождитесь когда администратор активирует вашу запись.')
        self.assertEqual(messages_list[0].tags, 'info')
        
        # Проверяем что логин остался в форме
        self.assertContains(response, 'value="inactiveuser"')
        
        # Проверяем задержку
        mock_sleep.assert_called_once_with(2)

    @patch('Chats.views.sleep')
    def test_login_wrong_password(self, mock_sleep):
        """Тест неверный пароль"""
        response = self.client.post(self.login_url, {
            'login': 'activeuser',
            'password': 'wrongpass'
        })
        
        # Проверяем что остаемся на странице логина
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Chats/login.html')
        
        # Проверяем что сессия не создана
        self.assertNotIn('user_id', self.client.session)
        self.assertNotIn('user_login', self.client.session)
        
        # Проверяем сообщение об ошибке
        messages_list = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), 'Неверный логин или пароль')
        self.assertEqual(messages_list[0].tags, 'error')
        
        # Проверяем что логин остался в форме
        self.assertContains(response, 'value="activeuser"')
        
        # Проверяем задержку
        mock_sleep.assert_called_once_with(2)

    @patch('Chats.views.sleep')
    def test_login_wrong_username(self, mock_sleep):
        """Тест несуществующий логин"""
        response = self.client.post(self.login_url, {
            'login': 'nonexistent',
            'password': 'anypass'
        })
        
        # Проверяем что остаемся на странице логина
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Chats/login.html')
        
        # Проверяем что сессия не создана
        self.assertNotIn('user_id', self.client.session)
        self.assertNotIn('user_login', self.client.session)
        
        # Проверяем сообщение об ошибке
        messages_list = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), 'Неверный логин или пароль')
        self.assertEqual(messages_list[0].tags, 'error')
        
        # Проверяем задержку
        mock_sleep.assert_called_once_with(2)

    @patch('Chats.views.sleep')
    def test_login_empty_credentials(self, mock_sleep):
        """Тест пустые данные"""
        test_cases = [
            {'login': '', 'password': ''},
            {'login': 'activeuser', 'password': ''},
            {'login': '', 'password': 'anypass'},
        ]
        
        for credentials in test_cases:
            with self.subTest(credentials=credentials):
                # Создаем новый клиент для каждого теста чтобы избежать накопления сообщений
                client = Client()
                
                response = client.post(self.login_url, credentials)
                
                # Проверяем что остаемся на странице логина
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, 'Chats/login.html')
                
                # Проверяем что сессия не создана
                self.assertNotIn('user_id', client.session)
                self.assertNotIn('user_login', client.session)
                
                # Проверяем сообщение об ошибке
                messages_list = list(get_messages(response.wsgi_request))
                self.assertGreaterEqual(len(messages_list), 1)
                # Берем последнее сообщение
                last_message = str(messages_list[-1])
                self.assertEqual(last_message, 'Неверный логин или пароль')
                
                # Проверяем задержку
                mock_sleep.assert_called_with(2)

    def test_login_session_created(self):
        """Тест проверки создания сессии (user_id, user_login)"""
        response = self.client.post(self.login_url, {
            'login': 'activeuser',
            'password': 'correctpass'
        })
        
        # Проверяем что сессия создана с правильными данными
        self.assertIn('user_id', self.client.session)
        self.assertEqual(self.client.session['user_id'], self.active_user.id)
        self.assertIn('user_login', self.client.session)
        self.assertEqual(self.client.session['user_login'], 'activeuser')
        
        # Проверяем что сессия persists между запросами
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Chats/home.html')

    def test_login_already_authenticated(self):
        """Тест редирект если уже авторизован"""
        # Сначала логинимся
        self.client.post(self.login_url, {
            'login': 'activeuser',
            'password': 'correctpass'
        })
        
        # Затем пытаемся зайти на страницу логина снова
        response = self.client.get(self.login_url)
        
        # Должен быть редирект на home
        self.assertRedirects(response, self.home_url)

    @patch('django_ratelimit.decorators.is_ratelimited')
    def test_login_rate_limit(self, mock_is_ratelimit):
        """Тест проверки rate limiting (10/5m для POST)"""
        # Имитируем превышение rate limit
        mock_is_ratelimit.return_value = True
        
        response = self.client.post(self.login_url, {
            'login': 'activeuser',
            'password': 'correctpass'
        })
        
        # Должен получить 429 Too Many Requests
        self.assertEqual(response.status_code, 429)
        
        # django-ratelimit возвращает HTML страницу с русским текстом
        # Проверяем что это действительно страница ошибки rate limit
        self.assertContains(response, 'Превышен лимит запросов', status_code=429)
        self.assertContains(response, 'слишком много запросов', status_code=429)

    @patch('Chats.views.sleep')
    def test_login_bruteforce_delay(self, mock_sleep):
        """Тест проверки задержки при неудачной попытке (2 сек)"""
        response = self.client.post(self.login_url, {
            'login': 'activeuser',
            'password': 'wrongpass'
        })
        
        # Проверяем что sleep был вызван с параметром 2
        mock_sleep.assert_called_once_with(2)
        
        # Проверяем что остаемся на странице логина
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Chats/login.html')
        
        # Проверяем сообщение об ошибке
        messages_list = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), 'Неверный логин или пароль')

    def test_login_session_data_persistence(self):
        """Тест сохранения данных сессии между запросами"""
        # Логинимся
        response = self.client.post(self.login_url, {
            'login': 'activeuser',
            'password': 'correctpass'
        })
        
        # Проверяем что сессия создана
        self.assertIn('user_id', self.client.session)
        self.assertIn('user_login', self.client.session)
        
        # Делаем несколько запросов и проверяем что сессия сохраняется
        for _ in range(3):
            response = self.client.get(self.home_url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(self.client.session['user_id'], self.active_user.id)
            self.assertEqual(self.client.session['user_login'], 'activeuser')

    def test_login_form_context_preservation(self):
        """Тест сохранения контекста формы при ошибках"""
        response = self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'wrongpass'
        })
        
        # Проверяем что логин сохранен в контексте
        self.assertEqual(response.context['login'], 'testuser')
        self.assertContains(response, 'value="testuser"')

    def test_login_csrf_protection(self):
        """Тест CSRF защиты"""
        # В тестах Django Client CSRF проверка отключена по умолчанию
        # Проверяем что с включенной CSRF проверкой получим 403
        client = Client(enforce_csrf_checks=True)
        response = client.post(self.login_url, {
            'login': 'activeuser',
            'password': 'correctpass'
        })
        self.assertEqual(response.status_code, 403)

    def test_login_with_whitespace_handling(self):
        """Тест обработки пробелов в логине"""
        # Создаем пользователя с пробелами в логине
        user_with_spaces = Users.objects.create(
            login='spaceduser',
            password_hash='hashed_pass',
            is_active=True
        )
        user_with_spaces.set_password('correctpass')
        user_with_spaces.save()
        
        # Пробуем войти с пробелами
        response = self.client.post(self.login_url, {
            'login': '  spaceduser  ',
            'password': 'correctpass'
        })
        
        # Должно сработать (т.к. login обрезается через strip())
        self.assertRedirects(response, self.home_url)
        self.assertIn('user_id', self.client.session)

    def test_login_case_sensitivity(self):
        """Тест чувствительности к регистру логина"""
        # Пробуем войти с другим регистром
        response = self.client.post(self.login_url, {
            'login': 'ACTIVEUSER',  # В верхнем регистре
            'password': 'correctpass'
        })
        
        # Не должно сработать (логин чувствителен к регистру)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('user_id', self.client.session)
        
        # Проверяем сообщение об ошибке
        messages_list = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), 'Неверный логин или пароль')
