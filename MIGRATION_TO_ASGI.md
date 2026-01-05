# Миграция с WSGI (Gunicorn) на ASGI (Uvicorn)

Приложение было мигрировано с синхронного WSGI сервера (Gunicorn) на асинхронный ASGI сервер (Uvicorn) для решения проблемы исчерпания воркеров при долгих запросах к OpenRouter API.

## Инструкция по развертыванию на production сервере:

1. **Обновить код и установить зависимости:**
```bash
cd /var/www/openrouterchats
git pull
source venv/bin/activate
pip install -r requirements.txt
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


## Локальная разработка - Запуск через manage.py (для разработки):
```bash
python manage.py runserver
```
Django автоматически использует ASGI если обнаруживает async views.

### Запуск через Uvicorn напрямую:
```bash
uvicorn OpenRouterChats.asgi:application --reload --host 0.0.0.0 --port 8000
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



