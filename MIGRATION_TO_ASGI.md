# Миграция с WSGI (Gunicorn) на ASGI (Uvicorn)

## Обзор изменений

Приложение было мигрировано с синхронного WSGI сервера (Gunicorn) на асинхронный ASGI сервер (Uvicorn) для решения проблемы исчерпания воркеров при долгих запросах к OpenRouter API.

### Основные преимущества

1. **Эффективность работы с долгими запросами** - один воркер может обрабатывать тысячи одновременных соединений во время ожидания I/O операций
2. **Меньше потребление памяти** - меньше воркеров для того же количества запросов
3. **Отсутствие блокировки** - долгие запросы к API (>30 сек) не блокируют другие запросы

## Что было изменено

### 1. Зависимости (`requirements.txt`)

**Удалено:**
- `gunicorn`

**Добавлено:**
- `uvicorn[standard]>=0.30.0` - ASGI сервер
- `httpx>=0.27.0` - асинхронная HTTP библиотека для запросов к OpenRouter API

### 2. Views (`OpenRouterChats/Chats/views.py`)

Следующие функции преобразованы в асинхронные:

- `send_message()` - **критично** - долгие запросы к OpenRouter API
- `get_all_models()` - запросы к OpenRouter API для получения списка моделей
- `get_all_teachers()` - запросы к БД
- `create_new_teacher()` - запросы к БД

**Ключевые изменения:**
- Добавлены `async def` вместо `def`
- Синхронные вызовы OpenRouter SDK заменены на асинхронные HTTP запросы через `httpx`
- Синхронные запросы к БД обернуты в `sync_to_async()`

**Пример изменения:**

```python
# До (синхронно, блокирует воркер)
def send_message(request):
    with OpenRouter(api_key=OPENROUTER_API_KEY) as client:
        response = client.chat.send(model=model, messages=messages)
        answer = response.choices[0].message.content

# После (асинхронно, не блокирует воркер)
async def send_message(request):
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={'Authorization': f'Bearer {OPENROUTER_API_KEY}', ...},
            json={'model': model, 'messages': messages}
        )
        answer = response.json()['choices'][0]['message']['content']
```

### 3. Systemd Service (`deploy/systemd/openrouterchats.service`)

**Изменено:**
- Description: `Gunicorn daemon` → `Uvicorn ASGI daemon`
- RuntimeDirectory: `gunicorn` → `uvicorn`
- ExecStart: команда запуска заменена с Gunicorn на Uvicorn

```ini
# До
ExecStart=/var/www/openrouterchats/venv/bin/gunicorn \
          --config /var/www/openrouterchats/gunicorn_config.py \
          OpenRouterChats.wsgi:application

# После
ExecStart=/var/www/openrouterchats/venv/bin/uvicorn \
          --host 127.0.0.1 \
          --port 8000 \
          --workers 4 \
          --log-level info \
          OpenRouterChats.asgi:application
```

### 4. Nginx конфигурация

**Не требует изменений** - Nginx продолжает проксировать на `127.0.0.1:8000`.

## Инструкция по развертыванию

### На production сервере:

1. **Обновить код и установить зависимости:**
```bash
cd /var/www/openrouterchats
git pull
source venv/bin/activate
pip install -r requirements.txt
```

2. **Применить миграции и собрать статику:**
```bash
cd OpenRouterChats
python manage.py migrate
python manage.py collectstatic --noinput
```

3. **Обновить systemd service:**
```bash
cp deploy/systemd/openrouterchats.service /etc/systemd/system/
systemctl daemon-reload
```

4. **Перезапустить сервис:**
```bash
systemctl restart openrouterchats
systemctl status openrouterchats
```

### Использование скрипта обновления:

```bash
# С обновлением зависимостей (первый раз после миграции)
./update_app.sh --req

# Обычное обновление
./update_app.sh
```

## Локальная разработка

### Запуск через manage.py (для разработки):
```bash
python manage.py runserver
```
Django автоматически использует ASGI если обнаруживает async views.

### Запуск через Uvicorn напрямую:
```bash
uvicorn OpenRouterChats.asgi:application --reload --host 0.0.0.0 --port 8000
```

### Запуск с несколькими воркерами (production-like):
```bash
uvicorn OpenRouterChats.asgi:application --host 127.0.0.1 --port 8000 --workers 4
```

## Настройка количества воркеров

**Рекомендации:**
- Для CPU-bound операций: `workers = (cpu_count * 2) + 1`
- Для I/O-bound операций (наш случай): `workers = cpu_count` или даже меньше

**Текущая настройка:** `--workers 4`

Это можно настроить в `deploy/systemd/openrouterchats.service` параметром `--workers`.

## Мониторинг и логи

### Просмотр логов:
```bash
journalctl -u openrouterchats -f
```

### Проверка статуса:
```bash
systemctl status openrouterchats
```

### Проверка активных соединений:
```bash
netstat -an | grep :8000
```

## Обратная совместимость

- Все синхронные views остались без изменений и продолжат работать
- Django автоматически определяет sync/async views и обрабатывает их соответственно
- Не требуется изменений в templates или frontend коде

## Troubleshooting

### Сервис не запускается

1. Проверьте логи: `journalctl -u openrouterchats -n 50`
2. Проверьте что uvicorn установлен: `which uvicorn`
3. Проверьте права доступа к директориям и файлам

### Долгие запросы всё ещё вызывают проблемы

1. Проверьте timeout в Nginx конфигурации (текущий: 120 секунд)
2. Проверьте timeout в httpx AsyncClient (текущий: 120 секунд)
3. Увеличьте количество воркеров если нужно

### Ошибки с базой данных

Убедитесь что синхронные ORM запросы обернуты в `sync_to_async()`:

```python
# Правильно
user = await sync_to_async(Users.objects.filter(id=user_id).first)()

# Неправильно (вызовет ошибку в async context)
user = Users.objects.filter(id=user_id).first()
```

## Откат на Gunicorn (если необходимо)

1. Установить gunicorn: `pip install gunicorn`
2. Восстановить старый systemd service из git истории
3. Reload daemon и restart service
4. Вернуть views.py в синхронную версию

**Примечание:** Не рекомендуется откатываться, так как это вернёт проблему с исчерпанием воркеров.
