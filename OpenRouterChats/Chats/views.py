from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from functools import wraps

from .models import Users
from openrouter import OpenRouter
from OpenRouterChats.settings import OPENROUTER_API_KEY
import json



def _require_login(view_func):
    """Проверка авторизации"""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('login')

        request.user_login = request.session.get('user_login')
        return view_func(request, *args, **kwargs)

    return _wrapped


@require_http_methods(['GET', 'POST'])
def login_view(request):
    """Вход"""
    if request.session.get('user_id'):
        return redirect('home')

    context = {}
    if request.method == 'POST':
        login = (request.POST.get('login') or '').strip()
        password = request.POST.get('password') or ''

        user = Users.objects.filter(login=login).first()
        if user and user.check_password(password):
            request.session['user_id'] = user.id
            request.session['user_login'] = user.login
            return redirect('home')

        context['error'] = 'Неверный логин или пароль'
        context['login'] = login

    return render(request, 'Chats/login.html', context)


def logout_view(request):
    """Выход"""
    request.session.flush()
    return redirect('login')


@_require_login
def home_view(request):
    """Главная"""
    user_login = getattr(request, 'user_login', None)

    chat_history = request.session.get('chat_history') or []
    error = request.session.pop('chat_error', None)

    return render(
        request,
        'Chats/home.html',
        {
            'login': user_login,
            'chat_history': chat_history,
            'error': error,
        },
    )


def get_all_models():
    """Получение списка моделей open_router"""
    with OpenRouter(api_key=OPENROUTER_API_KEY, ) as open_router:

        res = open_router.models.list()

        # Handle response
        print(res)
        
    return res



@_require_login
@require_http_methods(['POST'])
def send_message(request):
    """Отправка сообщения"""

    message = (request.POST.get('message') or '').strip()
    if not message:
        request.session['chat_error'] = 'Сообщение не может быть пустым.'
        return redirect('home')

    chat_history = request.session.get('chat_history') or []
    chat_history.append({'role': 'user', 'content': message})

    model = "tngtech/deepseek-r1t2-chimera:free"
    messages_for_model = chat_history[-20:]

    try:
        with OpenRouter(api_key=OPENROUTER_API_KEY) as client:
            response = client.chat.send(
                model=model,
                messages=messages_for_model,
            )

            answer = response.choices[0].message.content

        chat_history.append({'role': 'assistant', 'content': answer})
        request.session['chat_history'] = chat_history
        return redirect('home')
    except Exception:
        request.session['chat_history'] = chat_history
        request.session['chat_error'] = 'Не удалось получить ответ от модели. Попробуйте ещё раз.'
        return redirect('home')