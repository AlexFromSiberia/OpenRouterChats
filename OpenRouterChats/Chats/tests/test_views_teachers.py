'''
Тесты для get_all_teachers:

1. test_get_teachers_requires_login - требует авторизации
2. test_get_teachers_returns_json - возвращает JSON
3. test_get_teachers_empty_list - пустой список учителей
4. test_get_teachers_list - список учителей с данными
5. test_get_teachers_sorted_by_name - сортировка по имени
6. test_get_teachers_fields - правильные поля (id, name)
7. test_get_teachers_no_prompt_in_response - промпт не возвращается
8. test_get_teachers_multiple - несколько учителей
9. test_get_teachers_get_method_only - только GET метод разрешен

Особенности тестирования:
- Проверка декоратора _require_login
- Проверка декоратора require_http_methods(['GET'])
- JSON структура ответа
- Сортировка учителей
- Фильтрация полей (только id, name)
- HTTP статус коды
'''

import pytest
from django.test import TestCase, Client
from django.urls import reverse
import json

from Chats.models import Users, Teachers


class TestGetAllTeachers(TestCase):
    """Тесты для get_all_teachers"""

    def setUp(self):
        """Подготовка данных для тестов"""
        self.client = Client()
        self.teachers_url = reverse('get_all_teachers')
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

    def test_get_teachers_requires_login(self):
        """Тест требует авторизации"""
        # Запрос без авторизации
        response = self.client.get(self.teachers_url)
        
        # Должен быть редирект на login
        self.assertRedirects(response, self.login_url)

    def test_get_teachers_returns_json(self):
        """Тест возвращает JSON"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Запрашиваем учителей
        response = self.client.get(self.teachers_url)
        
        # Проверяем что ответ JSON
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Проверяем что можно распарсить JSON
        json_data = json.loads(response.content)
        self.assertIsInstance(json_data, dict)
        self.assertIn('teachers', json_data)

    def test_get_teachers_empty_list(self):
        """Тест пустой список учителей"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Запрашиваем учителей (база пуста)
        response = self.client.get(self.teachers_url)
        
        # Проверяем статус код
        self.assertEqual(response.status_code, 200)
        
        # Проверяем JSON структуру
        json_data = json.loads(response.content)
        self.assertEqual(json_data['teachers'], [])

    def test_get_teachers_list(self):
        """Тест список учителей с данными"""
        # Создаем учителя
        teacher = Teachers.objects.create(
            name='Test Teacher',
            prompt='This is a test prompt'
        )
        
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Запрашиваем учителей
        response = self.client.get(self.teachers_url)
        
        # Проверяем статус код
        self.assertEqual(response.status_code, 200)
        
        # Проверяем JSON структуру
        json_data = json.loads(response.content)
        self.assertEqual(len(json_data['teachers']), 1)
        
        # Проверяем данные учителя
        teacher_data = json_data['teachers'][0]
        self.assertEqual(teacher_data['id'], teacher.id)
        self.assertEqual(teacher_data['name'], 'Test Teacher')

    def test_get_teachers_sorted_by_name(self):
        """Тест сортировка по имени"""
        # Создаем учителей в разном порядке
        teacher_z = Teachers.objects.create(name='Zebra Teacher')
        teacher_a = Teachers.objects.create(name='Apple Teacher')
        teacher_m = Teachers.objects.create(name='Middle Teacher')
        
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Запрашиваем учителей
        response = self.client.get(self.teachers_url)
        
        # Проверяем статус код
        self.assertEqual(response.status_code, 200)
        
        # Проверяем сортировку
        json_data = json.loads(response.content)
        teachers = json_data['teachers']
        
        # Должны быть отсортированы по имени
        self.assertEqual(teachers[0]['name'], 'Apple Teacher')
        self.assertEqual(teachers[1]['name'], 'Middle Teacher')
        self.assertEqual(teachers[2]['name'], 'Zebra Teacher')

    def test_get_teachers_fields(self):
        """Тест правильные поля (id, name)"""
        # Создаем учителя с полными данными
        teacher = Teachers.objects.create(
            name='Test Teacher',
            prompt='This is a detailed prompt for testing'
        )
        
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Запрашиваем учителей
        response = self.client.get(self.teachers_url)
        
        # Проверяем статус код
        self.assertEqual(response.status_code, 200)
        
        # Проверяем JSON структуру
        json_data = json.loads(response.content)
        teacher_data = json_data['teachers'][0]
        
        # Проверяем что только нужные поля
        self.assertEqual(set(teacher_data.keys()), {'id', 'name'})
        self.assertIn('id', teacher_data)
        self.assertIn('name', teacher_data)
        self.assertNotIn('prompt', teacher_data)
        self.assertNotIn('user', teacher_data)

    def test_get_teachers_no_prompt_in_response(self):
        """Тест промпт не возвращается"""
        # Создаем учителя с промптом
        teacher = Teachers.objects.create(
            name='Teacher With Prompt',
            prompt='This prompt should not be in response'
        )
        
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Запрашиваем учителей
        response = self.client.get(self.teachers_url)
        
        # Проверяем статус код
        self.assertEqual(response.status_code, 200)
        
        # Проверяем JSON структуру
        json_data = json.loads(response.content)
        teacher_data = json_data['teachers'][0]
        
        # Промпт не должен быть в ответе
        self.assertNotIn('prompt', teacher_data)
        
        # Но в базе данных он должен быть
        teacher_from_db = Teachers.objects.get(id=teacher.id)
        self.assertEqual(teacher_from_db.prompt, 'This prompt should not be in response')

    def test_get_teachers_multiple(self):
        """Тест несколько учителей"""
        # Создаем несколько учителей
        teachers_data = [
            {'name': 'Math Teacher', 'prompt': 'Teaches mathematics'},
            {'name': 'Science Teacher', 'prompt': 'Teaches science'},
            {'name': 'English Teacher', 'prompt': 'Teaches English'},
        ]
        
        created_teachers = []
        for data in teachers_data:
            teacher = Teachers.objects.create(**data)
            created_teachers.append(teacher)
        
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Запрашиваем учителей
        response = self.client.get(self.teachers_url)
        
        # Проверяем статус код
        self.assertEqual(response.status_code, 200)
        
        # Проверяем JSON структуру
        json_data = json.loads(response.content)
        teachers = json_data['teachers']
        
        # Проверяем количество
        self.assertEqual(len(teachers), 3)
        
        # Проверяем что все учители присутствуют
        returned_names = [t['name'] for t in teachers]
        expected_names = [t['name'] for t in teachers_data]
        self.assertEqual(set(returned_names), set(expected_names))
        
        # Проверяем что у каждого есть id и name
        for teacher in teachers:
            self.assertIn('id', teacher)
            self.assertIn('name', teacher)
            self.assertIsInstance(teacher['id'], int)
            self.assertIsInstance(teacher['name'], str)

    def test_get_teachers_get_method_only(self):
        """Тест только GET метод разрешен"""
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Проверяем POST метод (должен быть запрещен)
        response = self.client.post(self.teachers_url)
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
        
        # Проверяем PUT метод (должен быть запрещен)
        response = self.client.put(self.teachers_url)
        self.assertEqual(response.status_code, 405)
        
        # Проверяем DELETE метод (должен быть запрещен)
        response = self.client.delete(self.teachers_url)
        self.assertEqual(response.status_code, 405)
        
        # GET метод должен работать
        response = self.client.get(self.teachers_url)
        self.assertEqual(response.status_code, 200)

    def test_get_teachers_with_null_prompt(self):
        """Тест учителей с null промптом"""
        # Создаем учителя без промпта
        teacher = Teachers.objects.create(
            name='Teacher Without Prompt'
            # prompt остается None
        )
        
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Запрашиваем учителей
        response = self.client.get(self.teachers_url)
        
        # Проверяем статус код
        self.assertEqual(response.status_code, 200)
        
        # Проверяем JSON структуру
        json_data = json.loads(response.content)
        teacher_data = json_data['teachers'][0]
        
        # Проверяем данные учителя
        self.assertEqual(teacher_data['id'], teacher.id)
        self.assertEqual(teacher_data['name'], 'Teacher Without Prompt')

    def test_get_teachers_with_user_relation(self):
        """Тест учителей с привязкой к пользователю"""
        # Создаем учителя с привязкой к пользователю
        teacher = Teachers.objects.create(
            name='Teacher With User',
            prompt='Some prompt',
            user=self.user
        )
        
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Запрашиваем учителей
        response = self.client.get(self.teachers_url)
        
        # Проверяем статус код
        self.assertEqual(response.status_code, 200)
        
        # Проверяем JSON структуру
        json_data = json.loads(response.content)
        teacher_data = json_data['teachers'][0]
        
        # Пользователь не должен быть в ответе
        self.assertNotIn('user', teacher_data)
        self.assertEqual(teacher_data['id'], teacher.id)
        self.assertEqual(teacher_data['name'], 'Teacher With User')

    def test_get_teachers_ordering_stability(self):
        """Тест стабильности сортировки"""
        # Создаем учителей с одинаковыми именами
        teacher1 = Teachers.objects.create(name='Same Name')
        teacher2 = Teachers.objects.create(name='Same Name')
        
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Запрашиваем учителей несколько раз
        responses = []
        for _ in range(3):
            response = self.client.get(self.teachers_url)
            json_data = json.loads(response.content)
            responses.append(json_data['teachers'])
        
        # Проверяем что порядок одинаков (сортировка по id для одинаковых имен)
        for response_teachers in responses[1:]:
            self.assertEqual(responses[0], response_teachers)

    def test_get_teachers_response_structure(self):
        """Тест структуры JSON ответа"""
        # Создаем учителя
        teacher = Teachers.objects.create(name='Test Teacher')
        
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Запрашиваем учителей
        response = self.client.get(self.teachers_url)
        
        # Проверяем полный ответ
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Проверяем JSON структуру
        json_data = json.loads(response.content)
        
        # Корневой элемент должен быть словарем
        self.assertIsInstance(json_data, dict)
        
        # Должен быть ключ 'teachers' со списком
        self.assertIn('teachers', json_data)
        self.assertIsInstance(json_data['teachers'], list)
        
        # Каждый элемент списка должен быть словарем с нужными полями
        for teacher in json_data['teachers']:
            self.assertIsInstance(teacher, dict)
            self.assertIn('id', teacher)
            self.assertIn('name', teacher)
            self.assertIsInstance(teacher['id'], int)
            self.assertIsInstance(teacher['name'], str)

    def test_get_teachers_large_dataset(self):
        """Тест большого набора данных"""
        # Создаем много учителей
        teachers = []
        for i in range(50):
            teacher = Teachers.objects.create(name=f'Teacher {i:02d}')
            teachers.append(teacher)
        
        # Логинимся
        self.client.post(self.login_url, {
            'login': 'testuser',
            'password': 'testpass123'
        })
        
        # Запрашиваем учителей
        response = self.client.get(self.teachers_url)
        
        # Проверяем статус код
        self.assertEqual(response.status_code, 200)
        
        # Проверяем JSON структуру
        json_data = json.loads(response.content)
        returned_teachers = json_data['teachers']
        
        # Проверяем количество
        self.assertEqual(len(returned_teachers), 50)
        
        # Проверяем сортировку
        names = [t['name'] for t in returned_teachers]
        self.assertEqual(names, sorted(names))
