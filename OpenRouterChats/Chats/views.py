from time import sleep
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.contrib import messages
from django.db import DatabaseError, IntegrityError, models
from functools import wraps

from .models import Teachers, Users
from openrouter import OpenRouter
from OpenRouterChats.settings import OPENROUTER_API_KEY

# название LLM по умолчанию
DEFAULT_LLM_MODEL = "tngtech/deepseek-r1t2-chimera:free"

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
            if not user.is_active:
                messages.info(request, 'Логин и пароль верные, дождитесь когда администратор активирует вашу запись.')
                context['login'] = login
                return render(request, 'Chats/login.html', context)

            request.session['user_id'] = user.id
            request.session['user_login'] = user.login
            return redirect('home')

        messages.error(request, 'Неверный логин или пароль')
        context['login'] = login

    return render(request, 'Chats/login.html', context)


@require_http_methods(['GET', 'POST'])
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

        if password != password2:
            messages.error(request, 'Пароли не совпадают')
            return render(request, 'Chats/register.html', context)

        if Users.objects.filter(login=login).exists():
            # Добавляем задержку для защиты от брутфорса
            sleep(3)
            messages.error(request, 'Пользователь с таким логином уже существует')
            return render(request, 'Chats/register.html', context)

        user = Users(login=login)
        user.set_password(password)
        #user.is_active = False
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


@_require_login
@require_http_methods(['POST'])
def clear_chat(request):
    """Очистка истории чата"""
    request.session.pop('chat_history', None)
    messages.success(request, 'Чат очищен.')
    return redirect('home')


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


@_require_login
@require_http_methods(['GET'])
def get_all_models(request):
    """Получение списка моделей open_router"""
    try:
        with OpenRouter(api_key=OPENROUTER_API_KEY) as open_router:
            res = open_router.models.list()

        model_ids = _extract_model_ids(res)
        free_models = sorted({m for m in model_ids if isinstance(m, str) and m.endswith(':free')})
        return JsonResponse({'models': free_models})
    except Exception:
        return JsonResponse({'models': []}, status=502)


@_require_login
@require_http_methods(['GET'])
def get_all_teachers(request):
    """Получение списка учителей"""
    #user_id = request.session.get('user_id')

    qs = Teachers.objects.all()
    # if user_id:
    #     qs = qs.filter(models.Q(user__isnull=True) | models.Q(user_id=user_id))

    teachers = list(qs.order_by('name', 'id').values('id', 'name'))
    return JsonResponse({'teachers': teachers})


@_require_login
@require_http_methods(['POST'])
def send_message(request):
    """Отправка сообщения"""

    message = (request.POST.get('message') or '').strip()
    if not message:
        messages.error(request, 'Сообщение не может быть пустым.')
        return redirect('home')
    
    chat_history = request.session.get('chat_history', [])
    teacher_id = (request.POST.get('teacher') or request.session.get('selected_teacher') or '').strip()
    

    
    chat_history.append({'role': 'user', 'content': message})
    
    model = (request.POST.get('model') or request.session.get('selected_model') or DEFAULT_LLM_MODEL).strip()
    if not model.endswith(':free'):
        request.session['chat_history'] = chat_history
        messages.error(request, 'Выберите бесплатную модель (:free).')
        return redirect('home')

    request.session['selected_model'] = model
    messages_for_model = chat_history[-20:]
    if teacher_id:
        request.session['selected_teacher'] = teacher_id
        prompt = [{'role': 'user', 'content': Teachers.objects.get(id=teacher_id).prompt}]
    
        if not messages_for_model or (messages_for_model and prompt[0] != messages_for_model[0]):
            messages_for_model = prompt + messages_for_model

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
        messages.error(request, 'Не удалось получить ответ от модели. Попробуйте ещё раз.')
        return redirect('home')


@_require_login
@require_http_methods(['POST'])
def create_new_teacher(request):
    """Создать нового учителя"""
    name = (request.POST.get('name') or '').strip()
    prompt = (request.POST.get('prompt') or '').strip()

    if not name:
        messages.error(request, 'Имя учителя обязательно.')
        return redirect('home')

    if not prompt:
        messages.error(request, 'Описание учителя обязательно.')
        return redirect('home')

    user = Users.objects.filter(id=request.session.get('user_id')).first()

    try:
        teacher = Teachers.objects.create(
            name=name,
            prompt=prompt,
            user=user,
        )
        request.session['selected_teacher'] = str(teacher.id)
        messages.success(request, 'Учитель добавлен.')
    except (IntegrityError, DatabaseError):
        messages.error(request, 'Не удалось создать учителя. Попробуйте ещё раз.')

    return redirect('home')

