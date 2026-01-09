'''
## Тесты для get_all_models

- test_get_models_requires_login - требует авторизации
- test_get_models_success - успешное получение с моком OpenRouter API
- test_get_models_filters_free_only - только модели с :free
- test_get_models_sorted - модели отсортированы
- test_get_models_api_error - обработка ошибки API (502)
- test_get_models_empty_response - пустой список моделей
- test_get_models_rate_limit - проверка rate limiting (5/m)
- test_get_models_async_execution - асинхронное выполнение
- test_extract_model_ids_various_formats - тест вспомогательной функции
Все тесты используют правильные моки для асинхронного httpx.AsyncClient с учетом того, 
что response.json() асинхронный, а response.raise_for_status() синхронный.
'''

import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.sessions.backends.db import SessionStore
from django.conf import settings
from Chats.models import Users
from Chats.views import _extract_model_ids


class GetAllModelsTestCase(TestCase):
    """Тесты для функции get_all_models"""
    
    def setUp(self):
        """Настройка тестового окружения"""
        self.client = Client()
        
        self.user = Users.objects.create(
            login='testuser',
            password_hash='hashedpassword',
            type='user',
            is_active=True
        )
        
        session = SessionStore()
        session['user_id'] = self.user.id
        session['user_login'] = self.user.login
        session.save()
        
        self.client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
    
    def test_get_models_requires_login(self):
        """Тест 1: Проверка требования авторизации"""
        session = SessionStore()
        session.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
        
        response = self.client.get(reverse('get_all_models'))
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    @patch('Chats.views.httpx.AsyncClient')
    def test_get_models_success(self, mock_async_client):
        """Тест 2: Успешное получение моделей с моком OpenRouter API"""
        mock_client_instance = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json = AsyncMock(return_value={
            'data': [
                {'id': 'openai/gpt-3.5-turbo:free', 'name': 'GPT-3.5 Turbo'},
                {'id': 'meta-llama/llama-3.2-3b-instruct:free', 'name': 'Llama 3.2 3B'},
                {'id': 'google/gemini-flash-1.5:free', 'name': 'Gemini Flash'},
            ]
        })
        
        mock_client_instance.get.return_value = mock_response
        
        response = self.client.get(reverse('get_all_models'))
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('models', data)
        self.assertEqual(len(data['models']), 3)
        self.assertIn('openai/gpt-3.5-turbo:free', data['models'])
    
    @patch('Chats.views.httpx.AsyncClient')
    def test_get_models_filters_free_only(self, mock_async_client):
        """Тест 3: Фильтрация моделей - только модели с :free"""
        mock_client_instance = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json = AsyncMock(return_value={
            'data': [
                {'id': 'openai/gpt-3.5-turbo:free', 'name': 'GPT-3.5 Turbo Free'},
                {'id': 'openai/gpt-4', 'name': 'GPT-4'},
                {'id': 'meta-llama/llama-3.2-3b-instruct:free', 'name': 'Llama 3.2 3B Free'},
                {'id': 'anthropic/claude-3-opus', 'name': 'Claude 3 Opus'},
                {'id': 'google/gemini-flash-1.5:free', 'name': 'Gemini Flash Free'},
            ]
        })
        
        mock_client_instance.get.return_value = mock_response
        
        response = self.client.get(reverse('get_all_models'))
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['models']), 3)
        
        for model in data['models']:
            self.assertTrue(model.endswith(':free'))
        
        self.assertNotIn('openai/gpt-4', data['models'])
        self.assertNotIn('anthropic/claude-3-opus', data['models'])
    
    @patch('Chats.views.httpx.AsyncClient')
    def test_get_models_sorted(self, mock_async_client):
        """Тест 4: Проверка сортировки моделей"""
        mock_client_instance = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json = AsyncMock(return_value={
            'data': [
                {'id': 'zeta/model:free'},
                {'id': 'alpha/model:free'},
                {'id': 'meta/model:free'},
                {'id': 'beta/model:free'},
            ]
        })
        
        mock_client_instance.get.return_value = mock_response
        
        response = self.client.get(reverse('get_all_models'))
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        models = data['models']
        
        self.assertEqual(models, sorted(models))
        self.assertEqual(models[0], 'alpha/model:free')
        self.assertEqual(models[-1], 'zeta/model:free')
    
    @patch('Chats.views.httpx.AsyncClient')
    def test_get_models_api_error(self, mock_async_client):
        """Тест 5: Обработка ошибки API (502)"""
        mock_client_instance = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception('API Error')
        mock_client_instance.get.return_value = mock_response
        
        response = self.client.get(reverse('get_all_models'))
        
        self.assertEqual(response.status_code, 502)
        data = json.loads(response.content)
        self.assertIn('models', data)
        self.assertEqual(data['models'], [])
    
    @patch('Chats.views.httpx.AsyncClient')
    def test_get_models_empty_response(self, mock_async_client):
        """Тест 6: Обработка пустого списка моделей"""
        mock_client_instance = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json = AsyncMock(return_value={'data': []})
        
        mock_client_instance.get.return_value = mock_response
        
        response = self.client.get(reverse('get_all_models'))
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('models', data)
        self.assertEqual(data['models'], [])
    
    @patch('Chats.views.httpx.AsyncClient')
    def test_get_models_rate_limit(self, mock_async_client):
        """Тест 7: Проверка rate limiting (5/m)"""
        mock_client_instance = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json = AsyncMock(return_value={'data': [{'id': 'test/model:free'}]})
        
        mock_client_instance.get.return_value = mock_response
        
        for i in range(5):
            response = self.client.get(reverse('get_all_models'))
            self.assertEqual(response.status_code, 200)
        
        response = self.client.get(reverse('get_all_models'))
        self.assertEqual(response.status_code, 429)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Rate limit exceeded')
    
    @patch('Chats.views.httpx.AsyncClient')
    def test_get_models_async_execution(self, mock_async_client):
        """Тест 8: Проверка асинхронного выполнения"""
        mock_client_instance = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json = AsyncMock(return_value={
            'data': [
                {'id': 'openai/gpt-3.5-turbo:free'},
            ]
        })
        
        mock_client_instance.get.return_value = mock_response
        
        response = self.client.get(reverse('get_all_models'))
        
        self.assertEqual(response.status_code, 200)
        
        mock_client_instance.get.assert_called_once()
        call_args = mock_client_instance.get.call_args
        self.assertEqual(call_args[0][0], 'https://openrouter.ai/api/v1/models')
        self.assertIn('Authorization', call_args[1]['headers'])


class TestExtractModelIds:
    """Тесты для вспомогательной функции _extract_model_ids"""
    
    def test_extract_model_ids_various_formats(self):
        """Тест 9: Извлечение ID моделей из различных форматов ответа"""
        
        response_with_data_dict = {
            'data': [
                {'id': 'model1:free', 'name': 'Model 1'},
                {'id': 'model2:free', 'name': 'Model 2'},
            ]
        }
        result = _extract_model_ids(response_with_data_dict)
        assert len(result) == 2
        assert 'model1:free' in result
        assert 'model2:free' in result
        
        response_with_models_dict = {
            'models': [
                {'id': 'model3:free'},
                {'id': 'model4:free'},
            ]
        }
        result = _extract_model_ids(response_with_models_dict)
        assert len(result) == 2
        assert 'model3:free' in result
        
        response_with_items_dict = {
            'items': [
                {'id': 'model5:free'},
            ]
        }
        result = _extract_model_ids(response_with_items_dict)
        assert len(result) == 1
        assert 'model5:free' in result
        
        response_with_name_field = {
            'data': [
                {'name': 'model6:free'},
                {'name': 'model7:free'},
            ]
        }
        result = _extract_model_ids(response_with_name_field)
        assert len(result) == 2
        assert 'model6:free' in result
        
        response_list_of_strings = ['model8:free', 'model9:free']
        result = _extract_model_ids(response_list_of_strings)
        assert len(result) == 2
        assert 'model8:free' in result
        
        response_none = None
        result = _extract_model_ids(response_none)
        assert result == []
        
        response_empty_dict = {}
        result = _extract_model_ids(response_empty_dict)
        assert result == []
        
        response_invalid_format = {'data': 'not a list'}
        result = _extract_model_ids(response_invalid_format)
        assert result == []
        
        response_nested_data = {
            'data': {
                'data': [
                    {'id': 'model10:free'},
                ]
            }
        }
        result = _extract_model_ids(response_nested_data)
        assert len(result) == 1
        assert 'model10:free' in result
        
        response_with_empty_ids = {
            'data': [
                {'id': ''},
                {'id': 'valid_model:free'},
                {'id': None},
            ]
        }
        result = _extract_model_ids(response_with_empty_ids)
        assert len(result) == 1
        assert 'valid_model:free' in result
