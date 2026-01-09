import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.contrib.sessions.backends.db import SessionStore
from django.conf import settings
from asgiref.sync import sync_to_async
from Chats.models import Teachers, Users


class SendMessageTestCase(TestCase):
    """Тесты для функции send_message"""
    
    def setUp(self):
        """Настройка тестового окружения"""
        self.client = Client()
        
        # Создание тестового пользователя
        self.user = Users.objects.create(
            login='testuser',
            password_hash='hashedpassword',
            type='user',
            is_active=True
        )
        
        # Создание тестового учителя
        self.teacher = Teachers.objects.create(
            name='Test Teacher',
            prompt='You are a helpful assistant.',
            user=self.user
        )
        
        # Настройка сессии
        session = SessionStore()
        session['user_id'] = self.user.id
        session['user_login'] = self.user.login
        session.save()
        
        # Установка сессии для клиента
        self.client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
        
        # Базовые данные для запроса
        self.base_data = {
            'message': 'Hello, how are you?',
            'chat_history': [],
            'teacher': str(self.teacher.id),
            'model': 'openai/gpt-3.5-turbo:free'
        }
    
    def tearDown(self):
        """Очистка после тестов"""
        # Очистка сообщений Django
        list(get_messages(self.client))
    
    def test_send_message_requires_login(self):
        """Тест 1: Проверка требования авторизации"""
        # Удаление user_id из сессии
        session = SessionStore()
        session.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
        
        response = self.client.post(
            reverse('send_message'),
            data=json.dumps(self.base_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    @patch('Chats.views.httpx.AsyncClient')
    def test_send_message_success(self, mock_async_client):
        """Тест 2: Успешная отправка сообщения с моком OpenRouter API"""
        # Настройка мока для асинхронного клиента
        mock_client_instance = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance
        
        # Создаем мок ответа
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = AsyncMock()
        
        # Настраиваем mock_response.json чтобы он возвращал нужный результат при вызове через await
        async def mock_json():
            return {
                'choices': [{
                    'message': {
                        'content': 'I am doing well, thank you!'
                    }
                }]
            }
        
        mock_response.json = mock_json
        mock_client_instance.post.return_value = mock_response
        
        # Выполнение запроса
        response = self.client.post(
            reverse('send_message'),
            data=json.dumps(self.base_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Проверка JSON ответа
        response_data = json.loads(response.content)
        self.assertIn('chat_history', response_data)
        self.assertEqual(len(response_data['chat_history']), 2)  # user message + bot response
        
        # Проверка истории чата
        chat_history = response_data['chat_history']
        self.assertEqual(chat_history[0]['role'], 'user')
        self.assertEqual(chat_history[0]['content'], 'Hello, how are you?')
        self.assertEqual(chat_history[1]['role'], 'assistant')
        self.assertEqual(chat_history[1]['content'], 'I am doing well, thank you!')
    
    def test_send_message_empty_message_error(self):
        """Тест 3: Ошибка при пустом сообщении (400)"""
        data = self.base_data.copy()
        data['message'] = ''
        
        response = self.client.post(
            reverse('send_message'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error'], 'Сообщение не может быть пустым.')
    
    def test_send_message_too_long_message_error(self):
        """Тест 4: Ошибка при сообщении длиннее 3000 символов (400)"""
        data = self.base_data.copy()
        data['message'] = 'a' * 3001  # 3001 символ
        
        response = self.client.post(
            reverse('send_message'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error'], 'Сообщение не может быть длиннее 3000 символов.')
    
    def test_send_message_no_teacher_selected_error(self):
        """Тест 5: Ошибка при отсутствии учителя (400)"""
        data = self.base_data.copy()
        data['teacher'] = ''
        
        response = self.client.post(
            reverse('send_message'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error'], 'Выберите учителя.')
    
    def test_send_message_no_model_selected_error(self):
        """Тест 6: Ошибка при отсутствии модели (400)"""
        data = self.base_data.copy()
        data['model'] = ''
        
        response = self.client.post(
            reverse('send_message'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error'], 'Выберите модель.')
    
    def test_send_message_model_without_free_error(self):
        """Тест 7: Ошибка при модели без :free (400)"""
        data = self.base_data.copy()
        data['model'] = 'openai/gpt-4'  # Без :free
        
        response = self.client.post(
            reverse('send_message'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error'], 'Выберите бесплатную модель (:free).')
    
    @patch('Chats.views.httpx.AsyncClient')
    def test_send_message_adds_to_chat_history(self, mock_async_client):
        """Тест 8: Добавление сообщения в историю чата"""
        # Настройка мока
        mock_client_instance = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(return_value={
            'choices': [{
                'message': {
                    'content': 'Response message'
                }
            }]
        })
        mock_client_instance.post.return_value = mock_response
        
        # Начальная история чата
        initial_history = [
            {'role': 'user', 'content': 'Previous message'},
            {'role': 'assistant', 'content': 'Previous response'}
        ]
        
        data = self.base_data.copy()
        data['chat_history'] = initial_history
        
        response = self.client.post(
            reverse('send_message'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        chat_history = response_data['chat_history']
        
        # Проверка, что история содержит предыдущие сообщения + новые
        self.assertEqual(len(chat_history), 4)
        self.assertEqual(chat_history[0]['content'], 'Previous message')
        self.assertEqual(chat_history[1]['content'], 'Previous response')
        self.assertEqual(chat_history[2]['content'], 'Hello, how are you?')
        self.assertEqual(chat_history[3]['content'], 'Response message')
    
    @patch('Chats.views.httpx.AsyncClient')
    def test_send_message_teacher_prompt_added_as_system_prompt(self, mock_async_client):
        """Тест 9: Промпт учителя добавляется как системный промпт"""
        # Настройка мока
        mock_client_instance = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance
        
        # Создаем мок ответа
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = AsyncMock()
        
        # Настраиваем mock_response.json чтобы он возвращал нужный результат при вызове через await
        async def mock_json():
            return {
                'choices': [{
                    'message': {
                        'content': 'Response'
                    }
                }]
            }
        
        mock_response.json = mock_json
        mock_client_instance.post.return_value = mock_response
        
        response = self.client.post(
            reverse('send_message'),
            data=json.dumps(self.base_data),
            content_type='application/json'
        )
        
        # Проверка, что системный промпт был добавлен к запросу
        mock_client_instance.post.assert_called_once()
        call_args = mock_client_instance.post.call_args
        
        # Проверка данных, отправленных в API
        request_data = call_args[1]['json']
        messages = request_data['messages']
        
        # Проверка наличия системного промпта (добавляется как user)
        user_messages = [msg for msg in messages if msg['role'] == 'user']
        prompt_messages = [msg for msg in user_messages if msg['content'] == 'You are a helpful assistant.']
        self.assertEqual(len(prompt_messages), 1)
    
    @patch('Chats.views.httpx.AsyncClient')
    def test_send_message_no_teacher_prompt_if_none(self, mock_async_client):
        """Тест 10: Нет промпта учителя, если у учителя его нет"""
        # Создание учителя без промпта
        teacher_no_prompt = Teachers.objects.create(
            name='No Prompt Teacher',
            prompt='',
            user=self.user
        )
        
        # Настройка мока
        mock_client_instance = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(return_value={
            'choices': [{
                'message': {
                    'content': 'Response'
                }
            }]
        })
        mock_client_instance.post.return_value = mock_response
        
        data = self.base_data.copy()
        data['teacher_id'] = teacher_no_prompt.id
        
        response = self.client.post(
            reverse('send_message'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Проверка отсутствия системного промпта
        mock_client_instance.post.assert_called_once()
        call_args = mock_client_instance.post.call_args
        
        # Проверка данных, отправленных в API
        request_data = call_args[1]['json']
        messages = request_data['messages']
        
        system_messages = [msg for msg in messages if msg['role'] == 'system']
        self.assertEqual(len(system_messages), 0)
    
    @patch('Chats.views.httpx.AsyncClient')
    def test_send_message_only_last_20_messages_to_model(self, mock_async_client):
        """Тест 11: Только последние 20 сообщений отправляются в модель"""
        # Настройка мока
        mock_client_instance = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(return_value={
            'choices': [{
                'message': {
                    'content': 'Response'
                }
            }]
        })
        mock_client_instance.post.return_value = mock_response
        
        # Создание истории с 25 сообщениями
        long_history = []
        for i in range(25):
            long_history.append({
                'role': 'user' if i % 2 == 0 else 'assistant',
                'content': f'Message {i}'
            })
        
        data = self.base_data.copy()
        data['chat_history'] = long_history
        
        response = self.client.post(
            reverse('send_message'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Проверка, что в модель отправлено только 20 сообщений + системный промпт
        mock_client_instance.post.assert_called_once()
        call_args = mock_client_instance.post.call_args
        
        request_data = call_args[1]['json']
        messages = request_data['messages']
        
        # 20 сообщений из истории + 1 новое сообщение пользователя = 21
        self.assertEqual(len(messages), 21)
        
        # Проверка, что отправлены последние 20 сообщений
        user_messages = [msg for msg in messages if msg['role'] == 'user']
        assistant_messages = [msg for msg in messages if msg['role'] == 'assistant']
        
        # Должно быть 12 пользовательских сообщений (11 из истории + 1 новое + промпт)
        self.assertEqual(len(user_messages), 12)
        # Должно быть 9 ассистентских сообщений (из истории)
        self.assertEqual(len(assistant_messages), 9)
    
    @patch('Chats.views.httpx.AsyncClient')
    def test_send_message_chat_history_limited_to_200(self, mock_async_client):
        """Тест 12: История чата ограничена 200 сообщениями в ответе"""
        # Настройка мока
        mock_client_instance = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(return_value={
            'choices': [{
                'message': {
                    'content': 'Response'
                }
            }]
        })
        mock_client_instance.post.return_value = mock_response
        
        # Создание истории с 199 сообщениями
        long_history = []
        for i in range(199):
            long_history.append({
                'role': 'user' if i % 2 == 0 else 'assistant',
                'content': f'Message {i}'
            })
        
        data = self.base_data.copy()
        data['chat_history'] = long_history
        
        response = self.client.post(
            reverse('send_message'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        chat_history = response_data['chat_history']
        
        # История должна быть ограничена 200 сообщениями
        self.assertEqual(len(chat_history), 200)
    
    @patch('Chats.views.httpx.AsyncClient')
    def test_send_message_openrouter_api_error(self, mock_async_client):
        """Тест 13: Обработка ошибок OpenRouter API (500)"""
        # Настройка мока для ошибки API
        mock_client_instance = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance
        
        # Мок ошибки API
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_client_instance.post.return_value = mock_response
        
        response = self.client.post(
            reverse('send_message'),
            data=json.dumps(self.base_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error'], 'Не удалось получить ответ от модели. Попробуйте ещё раз.')
    
    @patch('Chats.views.is_ratelimited')
    @patch('Chats.views.httpx.AsyncClient')
    def test_send_message_rate_limiting(self, mock_async_client, mock_is_ratelimited):
        """Тест 14: Rate limiting (30/m)"""
        # Настройка мока для rate limit
        mock_is_ratelimited.return_value = True
        
        # Настройка мока для API
        mock_client_instance = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(return_value={
            'choices': [{
                'message': {
                    'content': 'Response'
                }
            }]
        })
        mock_client_instance.post.return_value = mock_response
        
        response = self.client.post(
            reverse('send_message'),
            data=json.dumps(self.base_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 429)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error'], 'Rate limit exceeded')
    
    @patch('Chats.views.httpx.AsyncClient')
    def test_send_message_async_execution(self, mock_async_client):
        """Тест 15: Асинхронное выполнение"""
        # Настройка мока
        mock_client_instance = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(return_value={
            'choices': [{
                'message': {
                    'content': 'Async response'
                }
            }]
        })
        mock_client_instance.post.return_value = mock_response
        
        # Проверка, что был вызван асинхронный клиент
        response = self.client.post(
            reverse('send_message'),
            data=json.dumps(self.base_data),
            content_type='application/json'
        )
        
        # Проверка, что AsyncClient был использован
        mock_async_client.assert_called_once()
        self.assertEqual(response.status_code, 200)
    
    def test_send_message_http_methods_restriction(self):
        """Тест 16: Ограничение HTTP методов"""
        # Проверка GET запроса
        response = self.client.get(reverse('send_message'))
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
        
        # Проверка PUT запроса
        response = self.client.put(
            reverse('send_message'),
            data=json.dumps(self.base_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
        
        # Проверка DELETE запроса
        response = self.client.delete(reverse('send_message'))
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
    
    def test_send_message_invalid_json_format(self):
        """Тест 17: Некорректный JSON формат"""
        response = self.client.post(
            reverse('send_message'),
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error'], 'Invalid JSON format')
    
    def test_send_message_missing_required_fields(self):
        """Тест 18: Отсутствие обязательных полей"""
        # Тест без message
        data = {
            'chat_history': [],
            'teacher': str(self.teacher.id),
            'model': 'openai/gpt-3.5-turbo:free'
        }
        
        response = self.client.post(
            reverse('send_message'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
    
    @patch('Chats.views.httpx.AsyncClient')
    def test_send_message_database_error_handling(self, mock_async_client):
        """Тест 19: Обработка ошибок базы данных"""
        # Настройка мока для вызова ошибки при получении учителя
        with patch('Chats.views.Teachers.objects.get') as mock_get:
            mock_get.side_effect = Teachers.DoesNotExist
            
            response = self.client.post(
                reverse('send_message'),
                data=json.dumps(self.base_data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 500)
            response_data = json.loads(response.content)
            self.assertIn('error', response_data)
    
    @patch('Chats.views.httpx.AsyncClient')
    def test_send_message_network_error_handling(self, mock_async_client):
        """Тест 20: Обработка сетевых ошибок"""
        # Настройка мока для вызова сетевой ошибки
        mock_client_instance = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.post.side_effect = Exception('Network error')
        
        response = self.client.post(
            reverse('send_message'),
            data=json.dumps(self.base_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error'], 'Не удалось получить ответ от модели. Попробуйте ещё раз.')
