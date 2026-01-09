'''
RatelimitMiddleware (5 тестов):
    test_ratelimit_middleware_normal_request - обычный запрос проходит без изменений
    test_ratelimit_middleware_ajax_429 - AJAX запросы получают JSON ответ с ошибкой 429
    test_ratelimit_middleware_html_429 - обычные запросы получают HTML страницу 429.html
    test_ratelimit_middleware_exception_handling - правильная обработка исключения Ratelimited
    test_ratelimit_middleware_other_exception - другие исключения не обрабатываются

ContentSecurityPolicyMiddleware (6 тестов):
    test_csp_middleware_adds_header - добавляет CSP заголовок ко всем ответам
    test_csp_middleware_header_content - проверяет правильное содержимое CSP директив
    test_csp_middleware_all_pages - применяется ко всем страницам и URL
    test_csp_middleware_post_request - работает с POST запросами
    test_csp_middleware_ajax_request - работает с AJAX запросами
    test_csp_middleware_preserves_response - сохраняет исходный ответ и добавляет CSP
'''

import pytest
from django.test import Client, RequestFactory
from django.http import HttpResponse
from django_ratelimit.exceptions import Ratelimited
from unittest.mock import Mock, patch
from Chats.middleware import RatelimitMiddleware, ContentSecurityPolicyMiddleware


class TestRatelimitMiddleware:
    """Тесты для RatelimitMiddleware"""

    @pytest.fixture
    def middleware(self):
        """Фикстура для создания middleware"""
        def get_response(request):
            return HttpResponse("OK")
        return RatelimitMiddleware(get_response)

    @pytest.fixture
    def factory(self):
        """Фикстура для создания запросов"""
        return RequestFactory()

    def test_ratelimit_middleware_normal_request(self, middleware, factory):
        """Тест: обычный запрос проходит"""
        request = factory.get('/')
        response = middleware(request)
        
        assert response.status_code == 200
        assert response.content == b"OK"

    def test_ratelimit_middleware_ajax_429(self, middleware, factory):
        """Тест: AJAX запрос возвращает JSON 429"""
        request = factory.get('/')
        request.headers = {'X-Requested-With': 'XMLHttpRequest'}
        
        # Создаем исключение Ratelimited
        exception = Ratelimited()
        
        # Вызываем process_exception напрямую
        response = middleware.process_exception(request, exception)
        
        assert response.status_code == 429
        assert response['Content-Type'] == 'application/json'
        
        # Проверяем содержимое JSON
        import json
        content = json.loads(response.content.decode())
        assert content['error'] == 'Превышен лимит запросов. Пожалуйста, попробуйте позже.'

    def test_ratelimit_middleware_html_429(self, middleware, factory):
        """Тест: обычный запрос возвращает HTML 429"""
        request = factory.get('/')
        
        # Создаем исключение Ratelimited
        exception = Ratelimited()
        
        # Вызываем process_exception напрямую
        with patch('Chats.middleware.render') as mock_render:
            mock_render.return_value = HttpResponse("429 HTML", status=429)
            
            response = middleware.process_exception(request, exception)
            
            assert response.status_code == 429
            mock_render.assert_called_once_with(request, 'Chats/429.html', status=429)

    def test_ratelimit_middleware_exception_handling(self, middleware, factory):
        """Тест: правильная обработка Ratelimited"""
        request = factory.get('/')
        
        # Тестируем обработку исключения Ratelimited
        exception = Ratelimited()
        
        # Проверяем, что middleware обрабатывает именно Ratelimited
        with patch('Chats.middleware.render') as mock_render:
            mock_render.return_value = HttpResponse("429 HTML", status=429)
            
            response = middleware.process_exception(request, exception)
            
            assert response is not None
            assert response.status_code == 429
            mock_render.assert_called_once()

    def test_ratelimit_middleware_other_exception(self, middleware, factory):
        """Тест: другие исключения не обрабатываются"""
        request = factory.get('/')
        
        # Создаем другое исключение
        exception = ValueError("Test error")
        
        # Вызываем process_exception
        response = middleware.process_exception(request, exception)
        
        # Middleware не должен обрабатывать другие исключения
        assert response is None


class TestContentSecurityPolicyMiddleware:
    """Тесты для ContentSecurityPolicyMiddleware"""

    @pytest.fixture
    def middleware(self):
        """Фикстура для создания middleware"""
        def get_response(request):
            response = HttpResponse("OK")
            return response
        return ContentSecurityPolicyMiddleware(get_response)

    @pytest.fixture
    def factory(self):
        """Фикстура для создания запросов"""
        return RequestFactory()

    def test_csp_middleware_adds_header(self, middleware, factory):
        """Тест: добавляет CSP заголовок"""
        request = factory.get('/')
        response = middleware(request)
        
        assert 'Content-Security-Policy' in response
        assert response.status_code == 200

    def test_csp_middleware_header_content(self, middleware, factory):
        """Тест: правильное содержимое CSP"""
        request = factory.get('/')
        response = middleware(request)
        
        csp_header = response['Content-Security-Policy']
        
        # Проверяем основные директивы CSP
        assert "default-src 'self'" in csp_header
        assert "script-src 'self'" in csp_header
        assert "style-src 'self'" in csp_header
        assert "img-src 'self' data:" in csp_header
        assert "font-src 'self'" in csp_header
        assert "connect-src 'self'" in csp_header
        assert "frame-ancestors 'none'" in csp_header
        assert "base-uri 'self'" in csp_header
        assert "form-action 'self'" in csp_header

    def test_csp_middleware_all_pages(self, middleware, factory):
        """Тест: применяется ко всем страницам"""
        # Тестируем разные типы запросов
        urls = ['/', '/admin/', '/some/path/', '/api/test/']
        
        for url in urls:
            request = factory.get(url)
            response = middleware(request)
            
            assert 'Content-Security-Policy' in response
            csp_header = response['Content-Security-Policy']
            assert "default-src 'self'" in csp_header

    def test_csp_middleware_post_request(self, middleware, factory):
        """Тест: CSP применяется к POST запросам"""
        request = factory.post('/')
        response = middleware(request)
        
        assert 'Content-Security-Policy' in response
        assert response.status_code == 200

    def test_csp_middleware_ajax_request(self, middleware, factory):
        """Тест: CSP применяется к AJAX запросам"""
        request = factory.get('/')
        request.headers = {'X-Requested-With': 'XMLHttpRequest'}
        response = middleware(request)
        
        assert 'Content-Security-Policy' in response
        assert response.status_code == 200

    def test_csp_middleware_preserves_response(self, middleware, factory):
        """Тест: middleware не изменяет исходный ответ"""
        def get_response(request):
            response = HttpResponse("Original content")
            response['X-Custom-Header'] = 'custom-value'
            return response
        
        middleware_with_custom_response = ContentSecurityPolicyMiddleware(get_response)
        request = factory.get('/')
        response = middleware_with_custom_response(request)
        
        # Проверяем, что исходный ответ сохранен
        assert response.content == b"Original content"
        assert response['X-Custom-Header'] == 'custom-value'
        # И добавлен CSP заголовок
        assert 'Content-Security-Policy' in response
