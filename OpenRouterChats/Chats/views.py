from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .models import Users


def _require_login(request):
    """Проверка авторизации"""
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    return request.session.get('user_login')


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


def home_view(request):
    """Главная"""
    user_login = _require_login(request)
    if not user_login:
        return redirect('login')

    return render(request, 'Chats/home.html', {'login': user_login})
