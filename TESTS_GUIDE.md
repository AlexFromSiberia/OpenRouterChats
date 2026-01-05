## Тестовая инфраструктура для Django приложения OpenRouterChats успешно настроена:

**Для запуска тестов используйте:**
```bash
source .venv/bin/activate
export $(cat .env.test.clean | xargs)
python -m pytest OpenRouterChats/Chats/tests/test_models_users.py -v
```

**Для запуска всех тестов с покрытием:**
```bash
source .venv/bin/activate
export $(cat .env.test.clean | xargs)
python -m pytest --cov=OpenRouterChats --cov-report=term-missing
```

## Созданные файлы:
OpenRouterChats/Chats/tests/init.py - пустой файл для пакета тестов
OpenRouterChats/Chats/tests/conftest.py - pytest fixtures:
    client - тестовый клиент Django
    active_user - активный пользователь
    inactive_user - неактивный пользователь
    admin_user - администратор
    test_teacher - преподаватель с привязанным пользователем
    teacher_without_user - независимый преподаватель
    authenticated_client - авторизованный клиент
    authenticated_admin_client - авторизованный администратор
    multiple_users - несколько пользователей
    multiple_teachers - несколько преподавателей

requirements.txt - добавлены тестовые библиотеки:
    pytest>=8.0.0
    pytest-django>=4.5.0
    pytest-asyncio>=0.21.0
    pytest-cov>=4.0.0
    freezegun>=1.2.0

pytest.ini - настройки pytest для Django с покрытием кода и маркерами тестов
.env.test - тестовые переменные окружения с изолированной базой данных в памяти

## Особенности конфигурации:
    Тесты используют отдельную SQLite базу данных в памяти (:memory:)
    Отключены rate limiting и кэширование для тестов
    Настроено покрытие кода с порогом 80%
    Добавлены маркеры для категоризации тестов
    Ослаблены настройки безопасности для тестовой среды
