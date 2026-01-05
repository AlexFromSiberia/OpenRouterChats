'''
Тесты для home_view и logout_view:

home_view:
1. test_home_requires_login - неавторизованный редирект на login
2. test_home_authenticated_access - авторизованный пользователь видит страницу
3. test_home_displays_username - отображение имени пользователя
4. test_home_empty_chat_history - пустая история чата
5. test_home_with_chat_history - история чата из сессии

logout_view:
6. test_logout_clears_session - выход очищает сессию
7. test_logout_redirect_to_login - редирект на login
8. test_logout_without_auth - выход без авторизации тоже работает

Особенности тестирования:
- Проверка декоратора _require_login
- Работа с сессиями (user_id, user_login, chat_history)
- Контекст шаблонов (login, chat_history)
- Очистка сессии при выходе
- Редиректы для авторизованных/неавторизованных пользователей
'''

import pytest
from django.test import TestCase, Client
from django.urls import reverse

from Chats.models import Users


class TestHomeView(TestCase):
    """Тесты для home_view"""

    def setUp(self):
        """Подготовка данных для тестов"""
        self.client = Client()
        self.home_url = reverse('home')
        self.login_url = reverse('login')
        
        # Создаем тестового пользователя
        self.user = Users.objects.create(
            login='testuser',
            password_hash='hashed_pass',
            is_active=True
        )
        self.user.set_password('testpass123')
        self.user.save()

    def tearDown(self):
        """Очистка после каждого теста"""
        # Сбрасываем сессию
        self.client.session.flush()

    def test_home_requires_login(self):
        """Тест неавторизованный редирект на login"""
        response = self.client.get(self.home_url)
        
        # Должен быть редирект на login
        self.assertRedirects(response, self.login_url)
        
        # Проверяем что сессия не содержит данных пользователя
        self.assertNotIn('user_id', self.client.session)
        self.assertNotIn('user_login', self.client.session)

    def test_home_authenticated_access(self):
        """Тест авторизованный пользователь видит страницу"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Запрашиваем home
        response = self.client.get(self.home_url)
        
        # Проверяем успешный доступ
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Chats/home.html')
        
        # Проверяем что сессия содержит данные пользователя
        self.assertIn('user_id', self.client.session)
        self.assertIn('user_login', self.client.session)

    def test_home_displays_username(self):
        """Тест отображение имени пользователя"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Запрашиваем home
        response = self.client.get(self.home_url)
        
        # Проверяем что имя пользователя в контексте
        self.assertEqual(response.context['login'], 'testuser')
        
        # Проверяем что имя пользователя отображается в шаблоне
        self.assertContains(response, 'Привет, <strong>testuser</strong>!')

    def test_home_empty_chat_history(self):
        """Тест пустая история чата"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Запрашиваем home без истории чата
        response = self.client.get(self.home_url)
        
        # Проверяем что история чата пустая
        self.assertEqual(response.context['chat_history'], [])
        
        # Проверяем что в сессии нет истории чата
        self.assertNotIn('chat_history', self.client.session)
        # Или если есть, то пустая
        chat_history = self.client.session.get('chat_history', [])
        self.assertEqual(chat_history, [])

    def test_home_with_chat_history(self):
        """Тест история чата из сессии"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Добавляем историю чата в сессию
        chat_history = [
            {'role': 'user', 'content': 'Привет!'},
            {'role': 'assistant', 'content': 'Здравствуйте!'}
        ]
        session = self.client.session
        session['chat_history'] = chat_history
        session.save()
        
        # Запрашиваем home
        response = self.client.get(self.home_url)
        
        # Проверяем что история чата передана в контекст
        self.assertEqual(response.context['chat_history'], chat_history)
        
        # Проверяем что история чата сохранена в сессии
        self.assertEqual(self.client.session.get('chat_history'), chat_history)

    def test_home_session_data_persistence(self):
        """Тест сохранение данных сессии между запросами"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Добавляем историю чата
        chat_history = [{'role': 'user', 'content': 'Тест'}]
        session = self.client.session
        session['chat_history'] = chat_history
        session.save()
        
        # Делаем несколько запросов и проверяем что данные сохраняются
        for _ in range(3):
            response = self.client.get(self.home_url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['login'], 'testuser')
            self.assertEqual(response.context['chat_history'], chat_history)

    def test_home_user_login_attribute(self):
        """Тест установки атрибута request.user_login"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Запрашиваем home
        response = self.client.get(self.home_url)
        
        # Проверяем что атрибут user_login установлен в request
        # (проверяем через контекст, т.к. request не доступен напрямую в тестах)
        self.assertEqual(response.context['login'], 'testuser')

    def test_home_template_elements(self):
        """Тест элементов шаблона home"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Запрашиваем home
        response = self.client.get(self.home_url)
        
        # Проверяем основные элементы шаблона
        self.assertContains(response, 'Привет, <strong>testuser</strong>!')
        self.assertContains(response, 'Добавить нового учителя')
        self.assertContains(response, 'Очистить чат')
        self.assertContains(response, 'Ваше сообщение...')
        self.assertContains(response, 'Отправить')
        # Проверяем наличие CSRF токена через input
        self.assertContains(response, 'name="csrfmiddlewaretoken"')

    def test_home_different_users(self):
        """Тест разных пользователей"""
        # Создаем второго пользователя
        user2 = Users.objects.create(
            login='user2',
            password_hash='hashed_pass',
            is_active=True
        )
        user2.set_password('testpass123')
        user2.save()
        
        # Тест первого пользователя
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        response = self.client.get(self.home_url)
        self.assertEqual(response.context['login'], 'testuser')
        
        # Выход
        self.client.get(reverse('logout'))
        
        # Тест второго пользователя
        self.client.post(self.login_url, {
            'login': 'user2',
            'password': 'testpass123'
        })
        response = self.client.get(self.home_url)
        self.assertEqual(response.context['login'], 'user2')


class TestLogoutView(TestCase):
    """Тесты для logout_view"""

    def setUp(self):
        """Подготовка данных для тестов"""
        self.client = Client()
        self.logout_url = reverse('logout')
        self.login_url = reverse('login')
        self.home_url = reverse('home')
        
        # Создаем тестового пользователя
        self.user = Users.objects.create(
            login='testuser',
            password_hash='hashed_pass',
            is_active=True
        )
        self.user.set_password('testpass123')
        self.user.save()

    def tearDown(self):
        """Очистка после каждого теста"""
        # Сбрасываем сессию
        self.client.session.flush()

    def test_logout_clears_session(self):
        """Тест выход очищает сессию"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Проверяем что сессия содержит данные
        self.assertIn('user_id', self.client.session)
        self.assertIn('user_login', self.client.session)
        
        # Добавляем историю чата
        self.client.session['chat_history'] = [{'role': 'user', 'content': 'Test'}]
        self.client.session.save()
        
        # Выходим
        response = self.client.get(self.logout_url)
        
        # Проверяем что сессия очищена
        self.assertNotIn('user_id', self.client.session)
        self.assertNotIn('user_login', self.client.session)
        self.assertNotIn('chat_history', self.client.session)

    def test_logout_redirect_to_login(self):
        """Тест редирект на login"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Выходим
        response = self.client.get(self.logout_url)
        
        # Проверяем редирект на login
        self.assertRedirects(response, self.login_url)

    def test_logout_without_auth(self):
        """Тест выход без авторизации тоже работает"""
        # Выходим без авторизации
        response = self.client.get(self.logout_url)
        
        # Должен быть редирект на login
        self.assertRedirects(response, self.login_url)
        
        # Сессия должна быть пустой
        self.assertNotIn('user_id', self.client.session)
        self.assertNotIn('user_login', self.client.session)

    def test_logout_with_chat_history(self):
        """Тест выход с историей чата"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Добавляем историю чата
        chat_history = [
            {'role': 'user', 'content': 'Сообщение 1'},
            {'role': 'assistant', 'content': 'Ответ 1'},
            {'role': 'user', 'content': 'Сообщение 2'}
        ]
        session = self.client.session
        session['chat_history'] = chat_history
        session.save()
        
        # Проверяем что история есть
        self.assertEqual(self.client.session.get('chat_history'), chat_history)
        
        # Выходим
        response = self.client.get(self.logout_url)
        
        # Проверяем что история чата очищена
        self.assertIsNone(self.client.session.get('chat_history'))

    def test_logout_session_flush(self):
        """Тест полного сброса сессии"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Добавляем различные данные в сессию
        session = self.client.session
        session['test_key'] = 'test_value'
        session['another_key'] = {'nested': 'data'}
        session['chat_history'] = [{'role': 'user', 'content': 'Test'}]
        session.save()
        
        # Проверяем что данные есть
        self.assertEqual(self.client.session.get('test_key'), 'test_value')
        self.assertEqual(self.client.session.get('another_key'), {'nested': 'data'})
        self.assertIsNotNone(self.client.session.get('chat_history'))
        
        # Выходим
        response = self.client.get(self.logout_url)
        
        # Проверяем что все данные сессии очищены
        self.assertIsNone(self.client.session.get('test_key'))
        self.assertIsNone(self.client.session.get('another_key'))
        self.assertIsNone(self.client.session.get('chat_history'))
        self.assertIsNone(self.client.session.get('user_id'))
        self.assertIsNone(self.client.session.get('user_login'))

    def test_logout_multiple_times(self):
        """Тест многократного выхода"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Выходим несколько раз
        for i in range(3):
            response = self.client.get(self.logout_url)
            self.assertRedirects(response, self.login_url)
            
            # После первого выхода сессия должна быть пуста
            if i == 0:
                self.assertNotIn('user_id', self.client.session)
                self.assertNotIn('user_login', self.client.session)

    def test_logout_then_access_home(self):
        """Тест доступа к home после выхода"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Проверяем доступ к home
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        
        # Выходим
        self.client.get(self.logout_url)
        
        # Проверяем что доступ к home теперь запрещен
        response = self.client.get(self.home_url)
        self.assertRedirects(response, self.login_url)

    def test_logout_preserves_csrf_token(self):
        """Тест сохранения CSRF токена после выхода"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Выходим
        response = self.client.get(self.logout_url)
        
        # Проверяем что можем делать POST запросы (CSRF токен должен быть)
        response = self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        # Не должно быть ошибки CSRF, должен быть нормальный ответ
        self.assertIn(response.status_code, [200, 302])
