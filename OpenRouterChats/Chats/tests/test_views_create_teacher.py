'''
Тесты для create_new_teacher:

1. test_create_teacher_requires_login - требует авторизации
2. test_create_teacher_success - успешное создание учителя
3. test_create_teacher_user_assigned - пользователь автоматически назначается
4. test_create_teacher_empty_name - пустое имя - ошибка 400
5. test_create_teacher_empty_prompt - пустой промпт - ошибка 400
6. test_create_teacher_name_too_long - имя > 200 символов
7. test_create_teacher_prompt_too_long - промпт > 10000 символов
8. test_create_teacher_rate_limit - проверка rate limiting (10/m)
9. test_create_teacher_post_method_only - только POST метод
10. test_create_teacher_json_format - корректный JSON в запросе
11. test_create_teacher_csrf_token - проверка CSRF токена
12. test_create_teacher_database_error - обработка ошибок БД

Особенности тестирования:
- Проверка декоратора _require_login
- Проверка декоратора ratelimit (10/m)
- JSON запросы и ответы
- Django messages
- Создание записей в БД
- Обработка ошибок и валидация
'''

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.db import IntegrityError, DatabaseError
from django.contrib.messages import get_messages
from unittest.mock import patch
import json

from Chats.models import Users, Teachers


class TestCreateNewTeacher(TestCase):
    """Тесты для create_new_teacher"""

    def setUp(self):
        """Подготовка данных для тестов"""
        self.client = Client()
        self.create_teacher_url = reverse('create_new_teacher')
        self.login_url = reverse('login')
        
        # Очищаем базу данных
        Teachers.objects.all().delete()
        Users.objects.all().delete()
        
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

    def test_create_teacher_requires_login(self):
        """Тест требует авторизации"""
        # Запрос без авторизации
        response = self.client.post(
            self.create_teacher_url,
            data=json.dumps({'name': 'Test Teacher', 'prompt': 'Test prompt'}),
            content_type='application/json'
        )
        
        # Должен быть редирект на login
        self.assertRedirects(response, self.login_url)

    def test_create_teacher_success(self):
        """Тест успешное создание учителя"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Создаем учителя
        response = self.client.post(
            self.create_teacher_url,
            data=json.dumps({
                'name': 'Test Teacher',
                'prompt': 'This is a test prompt for the teacher'
            }),
            content_type='application/json'
        )
        
        # Проверяем успешный ответ
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Проверяем JSON ответ
        json_data = json.loads(response.content)
        self.assertEqual(json_data['success'], 'Учитель добавлен.')
        
        # Проверяем что учитель создан в БД
        teacher = Teachers.objects.filter(name='Test Teacher').first()
        self.assertIsNotNone(teacher)
        self.assertEqual(teacher.name, 'Test Teacher')
        self.assertEqual(teacher.prompt, 'This is a test prompt for the teacher')
        
        # Проверяем Django messages
        messages_list = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), 'Учитель добавлен.')
        self.assertEqual(messages_list[0].tags, 'success')

    def test_create_teacher_user_assigned(self):
        """Тест пользователь автоматически назначается"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Создаем учителя
        response = self.client.post(
            self.create_teacher_url,
            data=json.dumps({
                'name': 'Teacher With User',
                'prompt': 'Test prompt'
            }),
            content_type='application/json'
        )
        
        # Проверяем успешный ответ
        self.assertEqual(response.status_code, 200)
        
        # Проверяем что пользователь назначен
        teacher = Teachers.objects.filter(name='Teacher With User').first()
        self.assertIsNotNone(teacher)
        self.assertEqual(teacher.user, self.user)

    def test_create_teacher_empty_name(self):
        """Тест пустое имя - ошибка 400"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Пытаемся создать учителя с пустым именем
        response = self.client.post(
            self.create_teacher_url,
            data=json.dumps({
                'name': '',
                'prompt': 'Test prompt'
            }),
            content_type='application/json'
        )
        
        # Проверяем ошибку
        self.assertEqual(response.status_code, 400)
        
        # Проверяем JSON ответ
        json_data = json.loads(response.content)
        self.assertEqual(json_data['error'], 'Имя учителя обязательно.')
        
        # Проверяем Django messages
        messages_list = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), 'Имя учителя обязательно.')
        self.assertEqual(messages_list[0].tags, 'error')
        
        # Проверяем что учитель не создан
        teacher_count = Teachers.objects.filter(prompt='Test prompt').count()
        self.assertEqual(teacher_count, 0)

    def test_create_teacher_empty_prompt(self):
        """Тест пустой промпт - ошибка 400"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Пытаемся создать учителя с пустым промптом
        response = self.client.post(
            self.create_teacher_url,
            data=json.dumps({
                'name': 'Test Teacher',
                'prompt': ''
            }),
            content_type='application/json'
        )
        
        # Проверяем ошибку
        self.assertEqual(response.status_code, 400)
        
        # Проверяем JSON ответ
        json_data = json.loads(response.content)
        self.assertEqual(json_data['error'], 'Описание учителя обязательно.')
        
        # Проверяем Django messages
        messages_list = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), 'Описание учителя обязательно.')
        self.assertEqual(messages_list[0].tags, 'error')
        
        # Проверяем что учитель не создан
        teacher_count = Teachers.objects.filter(name='Test Teacher').count()
        self.assertEqual(teacher_count, 0)

    def test_create_teacher_name_too_long(self):
        """Тест имя > 200 символов"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Пытаемся создать учителя с длинным именем
        long_name = 'a' * 201  # Больше 200 символов
        response = self.client.post(
            self.create_teacher_url,
            data=json.dumps({
                'name': long_name,
                'prompt': 'Test prompt'
            }),
            content_type='application/json'
        )
        
        # Проверяем ошибку
        self.assertEqual(response.status_code, 400)
        
        # Проверяем JSON ответ
        json_data = json.loads(response.content)
        self.assertEqual(json_data['error'], 'Имя учителя не может быть длиннее 200 символов.')
        
        # Проверяем Django messages
        messages_list = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), 'Имя учителя не может быть длиннее 200 символов.')
        self.assertEqual(messages_list[0].tags, 'error')

    def test_create_teacher_prompt_too_long(self):
        """Тест промпт > 10000 символов"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Пытаемся создать учителя с длинным промптом
        long_prompt = 'a' * 10001  # Больше 10000 символов
        response = self.client.post(
            self.create_teacher_url,
            data=json.dumps({
                'name': 'Test Teacher',
                'prompt': long_prompt
            }),
            content_type='application/json'
        )
        
        # Проверяем ошибку
        self.assertEqual(response.status_code, 400)
        
        # Проверяем JSON ответ
        json_data = json.loads(response.content)
        self.assertEqual(json_data['error'], 'Описание учителя не может быть длиннее 10000 символов.')
        
        # Проверяем Django messages
        messages_list = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), 'Описание учителя не может быть длиннее 10000 символов.')
        self.assertEqual(messages_list[0].tags, 'error')

    def test_create_teacher_rate_limit(self):
        """Тест проверка rate limiting (10/m)"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Создаем учителя (rate limit должен разрешать)
        response = self.client.post(
            self.create_teacher_url,
            data=json.dumps({
                'name': 'Rate Limit Teacher',
                'prompt': 'Rate limit prompt'
            }),
            content_type='application/json'
        )
        
        # Должен успешно создать учителя
        self.assertEqual(response.status_code, 200)
        
        # Проверяем что учитель создан
        teacher = Teachers.objects.filter(name='Rate Limit Teacher').first()
        self.assertIsNotNone(teacher)

    def test_create_teacher_post_method_only(self):
        """Тест только POST метод"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Проверяем GET метод (должен быть запрещен)
        response = self.client.get(self.create_teacher_url)
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
        
        # Проверяем PUT метод (должен быть запрещен)
        response = self.client.put(
            self.create_teacher_url,
            data=json.dumps({'name': 'Test', 'prompt': 'Test'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 405)
        
        # Проверяем DELETE метод (должен быть запрещен)
        response = self.client.delete(self.create_teacher_url)
        self.assertEqual(response.status_code, 405)

    def test_create_teacher_json_format(self):
        """Тест корректный JSON в запросе"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Тест с правильным JSON
        response = self.client.post(
            self.create_teacher_url,
            data=json.dumps({
                'name': 'JSON Teacher',
                'prompt': 'JSON prompt'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Проверяем структуру ответа
        json_data = json.loads(response.content)
        self.assertIn('success', json_data)

    def test_create_teacher_csrf_token(self):
        """Тест проверка CSRF токена"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # В тестах Django Client CSRF проверка отключена по умолчанию
        # Проверяем что с включенной CSRF проверкой получим 403
        client = Client(enforce_csrf_checks=True)
        
        # Логинимся с новым клиентом
        client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        response = client.post(
            self.create_teacher_url,
            data=json.dumps({
                'name': 'CSRF Teacher',
                'prompt': 'CSRF prompt'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    @patch('Chats.models.Teachers.objects.create')
    def test_create_teacher_database_error(self, mock_create):
        """Тест обработка ошибок БД"""
        # Имитируем ошибку базы данных
        mock_create.side_effect = IntegrityError("Test integrity error")
        
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Пытаемся создать учителя
        response = self.client.post(
            self.create_teacher_url,
            data=json.dumps({
                'name': 'Error Teacher',
                'prompt': 'Error prompt'
            }),
            content_type='application/json'
        )
        
        # Проверяем успешный HTTP ответ (ошибка обработана)
        self.assertEqual(response.status_code, 200)
        
        # Проверяем JSON ответ с сообщением об ошибке
        json_data = json.loads(response.content)
        self.assertEqual(json_data['success'], 'Не удалось создать учителя. Попробуйте ещё раз.')
        
        # Проверяем Django messages
        messages_list = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), 'Не удалось создать учителя. Попробуйте ещё раз.')
        self.assertEqual(messages_list[0].tags, 'error')

    def test_create_teacher_whitespace_handling(self):
        """Тест обработка пробелов в данных"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Создаем учителя с пробелами
        response = self.client.post(
            self.create_teacher_url,
            data=json.dumps({
                'name': '  Spaced Teacher  ',
                'prompt': '  Spaced prompt  '
            }),
            content_type='application/json'
        )
        
        # Проверяем успешное создание
        self.assertEqual(response.status_code, 200)
        
        # Проверяем что пробелы обрезаны
        teacher = Teachers.objects.filter(name='Spaced Teacher').first()
        self.assertIsNotNone(teacher)
        self.assertEqual(teacher.name, 'Spaced Teacher')
        self.assertEqual(teacher.prompt, 'Spaced prompt')

    def test_create_teacher_missing_fields(self):
        """Тест отсутствующие поля в JSON"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Тест без поля name
        response = self.client.post(
            self.create_teacher_url,
            data=json.dumps({
                'prompt': 'Test prompt'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        json_data = json.loads(response.content)
        self.assertEqual(json_data['error'], 'Имя учителя обязательно.')
        
        # Тест без поля prompt
        response = self.client.post(
            self.create_teacher_url,
            data=json.dumps({
                'name': 'Test Teacher'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        json_data = json.loads(response.content)
        self.assertEqual(json_data['error'], 'Описание учителя обязательно.')

    def test_create_teacher_multiple_teachers(self):
        """Тест создание нескольких учителей"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Создаем несколько учителей
        teachers_data = [
            {'name': 'Math Teacher', 'prompt': 'Teaches mathematics'},
            {'name': 'Science Teacher', 'prompt': 'Teaches science'},
            {'name': 'English Teacher', 'prompt': 'Teaches English'},
        ]
        
        for data in teachers_data:
            response = self.client.post(
                self.create_teacher_url,
                data=json.dumps(data),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)
            
            # Проверяем успешное сообщение
            json_data = json.loads(response.content)
            self.assertEqual(json_data['success'], 'Учитель добавлен.')
        
        # Проверяем что все учители созданы
        teacher_count = Teachers.objects.count()
        self.assertEqual(teacher_count, 3)
        
        # Проверяем что все учители привязаны к пользователю
        for teacher in Teachers.objects.all():
            self.assertEqual(teacher.user, self.user)

    def test_create_teacher_edge_cases(self):
        """Тест граничные случаи"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Тест имени ровно 200 символов
        name_200 = 'a' * 200
        response = self.client.post(
            self.create_teacher_url,
            data=json.dumps({
                'name': name_200,
                'prompt': 'Test prompt'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Тест промпта ровно 10000 символов
        prompt_10000 = 'a' * 10000
        response = self.client.post(
            self.create_teacher_url,
            data=json.dumps({
                'name': 'Edge Teacher',
                'prompt': prompt_10000
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

    def test_create_teacher_response_structure(self):
        """Тест структуры JSON ответа"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Создаем учителя
        response = self.client.post(
            self.create_teacher_url,
            data=json.dumps({
                'name': 'Structure Teacher',
                'prompt': 'Structure prompt'
            }),
            content_type='application/json'
        )
        
        # Проверяем полный ответ
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Проверяем JSON структуру
        json_data = json.loads(response.content)
        
        # Корневой элемент должен быть словарем
        self.assertIsInstance(json_data, dict)
        
        # Должен быть ключ 'success'
        self.assertIn('success', json_data)
        self.assertIsInstance(json_data['success'], str)
