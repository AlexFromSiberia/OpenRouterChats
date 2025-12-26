# Скрипт обновления OpenRouterChats

## Установка  прав  !!!!!!!!
```bash
chmod +x update_app.sh
```

## Обзор
Скрипт `update_app.sh` для удаленного обновления Django приложения на сервере `94.154.11.231`.

## Использование
| Команда | Описание |
|---|---|
| `./update_app.sh` | Базовое обновление |
| `./update_app.sh --req` | С обновлением зависимостей |
| `./update_app.sh --help` | Справка |

## Что выполняет
1. `git pull` - обновление кода
2. `pip install -r requirements.txt` (только с `--req`)
3. `python manage.py migrate` - миграции БД
4. `python manage.py collectstatic --noinput` - сбор статики
5. `systemctl restart openrouterchats` - перезапуск сервиса
6. Проверка статуса сервиса


## Сервер
- **Хост:** 94.154.11.231:22
- **Пользователь:** root
- **Директория:** /var/www/openrouterchats
- **Сервис:** openrouterchats
