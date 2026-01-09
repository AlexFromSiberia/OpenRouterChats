import logging
from time import sleep
import json
import httpx
from asgiref.sync import sync_to_async
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.contrib import messages
from django.db import DatabaseError, IntegrityError, models
from functools import wraps
from django_ratelimit.decorators import ratelimit
from django_ratelimit.core import is_ratelimited

from .models import Teachers, Users
from OpenRouterChats.settings import OPENROUTER_API_KEY


logger = logging.getLogger(__name__)


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


def _require_login_async(view_func):
    """Проверка авторизации для асинхронных view"""
    @wraps(view_func)
    async def _wrapped(request, *args, **kwargs):
        # В асинхронном контексте нужно использовать sync_to_async для работы с сессией
        user_id = await sync_to_async(request.session.get)('user_id')
        if not user_id:
            return redirect('login')

        request.user_login = await sync_to_async(request.session.get)('user_login')
        return await view_func(request, *args, **kwargs)

    return _wrapped


def ratelimit_async(key, rate, method='ALL'):
    """Асинхронная версия декоратора ratelimit"""
    def decorator(view_func):
        @wraps(view_func)
        async def _wrapped(request, *args, **kwargs):
            # Используем sync_to_async для проверки rate limit
            ratelimited = await sync_to_async(is_ratelimited)(
                request=request,
                fn=view_func,  # Передаём функцию для правильной работы django-ratelimit
                key=key,
                rate=rate,
                method=method,
                increment=True
            )

            if ratelimited:
                return JsonResponse({'error': 'Rate limit exceeded'}, status=429)

            return await view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


@require_http_methods(['GET', 'POST'])
@ratelimit(key='ip', rate='10/5m', method='POST')
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
            if not user.is_active:
                sleep(2)
                messages.info(request, 'Логин и пароль верные, дождитесь когда администратор активирует вашу запись.')
                context['login'] = login
                return render(request, 'Chats/login.html', context)

            request.session['user_id'] = user.id
            request.session['user_login'] = user.login
            return redirect('home')

        # Защита от брутфорса
        sleep(2)
        messages.error(request, 'Неверный логин или пароль')
        context['login'] = login

    return render(request, 'Chats/login.html', context)


@require_http_methods(['GET', 'POST'])
@ratelimit(key='ip', rate='3/h', method='POST')
def register_view(request):
    """Регистрация нового пользователя (администратор активирует после проверки)
    """
    if request.session.get('user_id'):
        return redirect('home')

    context = {}
    if request.method == 'POST':
        login = (request.POST.get('login') or '').strip()
        password = request.POST.get('password') or ''
        password2 = request.POST.get('password2') or ''

        context['login'] = login

        if not login or not password:
            messages.error(request, 'Логин и пароль обязательны')
            return render(request, 'Chats/register.html', context)

        if len(login) > 150:
            messages.error(request, 'Логин не может быть длиннее 150 символов')
            return render(request, 'Chats/register.html', context)

        if password != password2:
            messages.error(request, 'Пароли не совпадают')
            return render(request, 'Chats/register.html', context)

        if len(password) > 128:
            messages.error(request, 'Пароль не может быть длиннее 128 символов')
            return render(request, 'Chats/register.html', context)        

        if len(password) < 8:
            messages.error(request, 'Пароль должен содержать не менее 8 символов')
            return render(request, 'Chats/register.html', context)        

        if Users.objects.filter(login=login).exists():
            # Добавляем задержку для защиты от брутфорса
            sleep(3)
            messages.error(request, 'Пользователь с таким логином уже существует')
            return render(request, 'Chats/register.html', context)

        user = Users(login=login)
        user.set_password(password)
        #By default user.is_active = False in Users model
        user.save()

        messages.info(request, 'Регистрация успешна. Дождитесь когда администратор активирует вашу запись.')
        return redirect('login')

    return render(request, 'Chats/register.html', context)


def logout_view(request):
    """Выход"""
    request.session.flush()
    return redirect('login')


@_require_login
def home_view(request):
    """Главная страница"""
    user_login = getattr(request, 'user_login', None)
    chat_history = request.session.get('chat_history') or []

    return render(
        request,
        'Chats/home.html',
        {
            'login': user_login,
            'chat_history': chat_history,
        },
    )


def _extract_model_ids(models_res):
    """Извлечение идентификаторов моделей из ответа openrouter
        - вспомогательная для get_all_models
    """
    if models_res is None:
        return []

    data = None
    if isinstance(models_res, dict):
        data = models_res.get('data') or models_res.get('models') or models_res.get('items')
    else:
        data = getattr(models_res, 'data', None) or getattr(models_res, 'models', None)

    if data is None:
        data = models_res

    if isinstance(data, dict):
        data = data.get('data') or data.get('models') or data.get('items')

    if not isinstance(data, (list, tuple)):
        return []

    model_ids = []
    for item in data:
        model_id = None
        if isinstance(item, str):
            model_id = item
        elif isinstance(item, dict):
            model_id = item.get('id') or item.get('name')
        else:
            model_id = getattr(item, 'id', None) or getattr(item, 'name', None)

        if isinstance(model_id, str) and model_id:
            model_ids.append(model_id)

    return model_ids


@_require_login_async
@require_http_methods(['GET'])
@ratelimit_async(key='ip', rate='5/m', method='GET')
async def get_all_models(request):
    """Получение списка моделей open_router"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                'https://openrouter.ai/api/v1/models',
                headers={'Authorization': f'Bearer {OPENROUTER_API_KEY}'}
            )
            response.raise_for_status()
            res = await response.json()

        model_ids = _extract_model_ids(res)
        free_models = sorted({m for m in model_ids if isinstance(m, str) and m.endswith(':free')})
        return JsonResponse({'models': free_models})
    except Exception as e:
        print(e)
        logger.exception("Failed to fetch OpenRouter models")
        return JsonResponse({'models': []}, status=502)


@_require_login
@require_http_methods(['GET'])
def get_all_teachers(request):
    """Получение списка учителей"""
    qs = Teachers.objects.all()
    teachers = list(qs.order_by('name', 'id').values('id', 'name'))
    return JsonResponse({'teachers': teachers})


@_require_login_async
@require_http_methods(['POST'])
@ratelimit_async(key='user_or_ip', rate='30/m', method='POST')
async def send_message(request):
    """Отправка сообщения"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    
    message = data.get('message', '').strip()
    chat_history = data.get('chat_history', [])
    teacher_id = data.get('teacher', '').strip()
    chat_history.append({'role': 'user', 'content': message})
    model = data.get('model').strip()
    messages_for_model = chat_history[-20:]

    if len(message) > 3000:
        messages.error(request, 'Сообщение не может быть длиннее 3000 символов.')
        return JsonResponse({'error': 'Сообщение не может быть длиннее 3000 символов.'}, status=400)
    if not message:
        messages.error(request, 'Сообщение не может быть пустым.')
        return JsonResponse({'error': 'Сообщение не может быть пустым.'}, status=400)
    if not teacher_id:
        messages.error(request, 'Выберите учителя.')
        return JsonResponse({'error': 'Выберите учителя.'}, status=400)
    if not model:
        messages.error(request, 'Выберите модель.')
        return JsonResponse({'error': 'Выберите модель.'}, status=400)
    if not model.endswith(':free'):
        messages.error(request, 'Выберите бесплатную модель (:free).')
        return JsonResponse({'error': 'Выберите бесплатную модель (:free).'}, status=400)

    teacher = await sync_to_async(Teachers.objects.filter(id=teacher_id).first, thread_sensitive=True)()
    teacher_prompt = (teacher.prompt or '').strip() if teacher else ''
    # Для чата БЕЗ учителя ничего не добавляем (учительский промт не вставляем в начало)
    # Учительский промт будет использован как системный контекст, если он есть
    if teacher_prompt:
        prompt = [{'role': 'user', 'content': teacher_prompt}]

        if not messages_for_model or (messages_for_model and prompt[0] != messages_for_model[0]):
            messages_for_model = prompt + messages_for_model

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {OPENROUTER_API_KEY}',
                    'Content-Type': 'application/json',
                },
                json={
                    'model': model,
                    'messages': messages_for_model,
                }
            )
            response.raise_for_status()
            result = await response.json()
            answer = result['choices'][0]['message']['content']

        chat_history.append({'role': 'assistant', 'content': answer})
        # limit chat history to 200 messages
        chat_history = chat_history[-200:]
        return JsonResponse({'chat_history': chat_history})
    except Exception as e:
        print(e)
        logger.exception("Failed to send chat message via OpenRouter")
        messages.error(request, 'Не удалось получить ответ от модели. Попробуйте ещё раз.')
        return JsonResponse({'error': 'Не удалось получить ответ от модели. Попробуйте ещё раз.'}, status=500)


@_require_login
@require_http_methods(['POST'])
@ratelimit(key='user_or_ip', rate='10/m', method='POST')
def create_new_teacher(request):
    """Создать нового учителя"""
    data = json.loads(request.body)
    name = data.get('name', '').strip()
    prompt = data.get('prompt', '').strip()

    if not name:
        messages.error(request, 'Имя учителя обязательно.')
        return JsonResponse({'error': 'Имя учителя обязательно.'}, status=400)

    if name and len(name) > 200:
        messages.error(request, 'Имя учителя не может быть длиннее 200 символов.')
        return JsonResponse({'error': 'Имя учителя не может быть длиннее 200 символов.'}, status=400)

    if not prompt:
        messages.error(request, 'Описание учителя обязательно.')
        return JsonResponse({'error': 'Описание учителя обязательно.'}, status=400)

    if prompt and len(prompt) > 10000:
        messages.error(request, 'Описание учителя не может быть длиннее 10000 символов.')
        return JsonResponse({'error': 'Описание учителя не может быть длиннее 10000 символов.'}, status=400)

    user = Users.objects.filter(id=request.session.get('user_id')).first()
    message = 'Учитель добавлен.'
    try:
        Teachers.objects.create(name=name, prompt=prompt, user=user)
        messages.success(request, message)
    except (IntegrityError, DatabaseError):
        message = 'Не удалось создать учителя. Попробуйте ещё раз.'
        messages.error(request, message)

    return JsonResponse({'success': message}, status=200)


@require_http_methods(['GET'])
def get_messages_view(request):
    """Получение сообщений Django messages через AJAX"""
    from django.contrib.messages import get_messages

    message_list = []
    storage = get_messages(request)
    for message in storage:
        message_list.append({
            'text': str(message),
            'tags': message.tags
        })

    return JsonResponse({'messages': message_list})

