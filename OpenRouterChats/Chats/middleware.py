from django_ratelimit.exceptions import Ratelimited
from django.http import JsonResponse
from django.shortcuts import render


class RatelimitMiddleware:
    """Middleware для обработки исключений превышения лимита запросов"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        """Перехватывает исключение Ratelimited и возвращает 429 ответ"""
        if isinstance(exception, Ratelimited):
            # Для AJAX: JSON {'error': '...'} с кодом 429
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': 'Превышен лимит запросов. Пожалуйста, попробуйте позже.'
                }, status=429)
            # Для обычных запросов: Возвращает HTML страницу 429.html с кодом 429
            return render(request, 'Chats/429.html', status=429)
        
        return None
