# Руководство по деплою OpenRouterChats на Ubuntu 22 VPS

## Подготовка проекта (локально)

Все необходимые изменения уже внесены в код:
- ✅ Настроены переменные окружения для production
- ✅ Добавлен WhiteNoise для статических файлов
- ✅ Настроены security settings для production
- ✅ Созданы конфигурационные файлы

## Шаг 1: Подготовка VPS

### 1.1 Подключитесь к серверу
```bash
ssh -p 22 root@94.154.11.231
```

### 1.2 Обновите систему
```bash
apt update && apt upgrade -y
```

### 1.3 Установите необходимые пакеты
```bash
apt install -y python3-venv python3-pip nginx git
```


## Шаг 2: Загрузка проекта на сервер

### 2.1 Создайте директорию для проекта
```bash
mkdir -p /var/www/openrouterchats
cd /var/www/openrouterchats
```

### 2.2 Загрузите проект (выберите один из вариантов)

**Вариант А: Через Git (рекомендуется)**
```bash
# Если проект в Git репозитории
git clone https://github.com/AlexFromSiberia/OpenRouterChats.git .
```

## Шаг 3: Настройка Python окружения

### 3.1 Создайте виртуальное окружение
```bash
cd /var/www/openrouterchats
python3 -m venv venv
source venv/bin/activate
```

### 3.2 Установите зависимости
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Шаг 4: Настройка переменных окружения

### 4.1 Создайте файл .env
```bash
nano /var/www/openrouterchats/.env
```

### 4.2 Добавьте следующие переменные (замените значения на свои):
```env
DEBUG=True
ALLOWED_HOSTS=151461.com,www.151461.com,151461.com,127.0.0.1,localhost,94.154.11.231
SECRET_KEY=000
OPENROUTER_API_KEY=000
DISABLE_SSL_REDIRECT=True

```

### 4.3 Генерация нового SECRET_KEY
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
Скопируйте вывод и используйте как SECRET_KEY в .env файле.

## Шаг 5: Настройка Django

### 5.1 Выполните миграции базы данных
```bash
cd /var/www/openrouterchats
source venv/bin/activate
cd OpenRouterChats
python manage.py migrate
```

### 5.2 Соберите статические файлы

проверить - staticfiles должны быть там же где и main.py !!!
```bash
python manage.py collectstatic --noinput
```

### 5.3 Создайте суперпользователя
```bash
python manage.py createsuperuser
```

### 5.4 Проверьте настройки
```bash
python manage.py check --deploy
```

## Шаг 6: Настройка Gunicorn

### 6.1 Создайте директорию для логов
```bash
mkdir -p /var/log/gunicorn
```

### 6.2 Проверьте работу Gunicorn
```bash
cd /var/www/openrouterchats/OpenRouterChats
source /var/www/openrouterchats/venv/bin/activate
gunicorn --config /var/www/openrouterchats/gunicorn_config.py OpenRouterChats.wsgi:application
```
Нажмите Ctrl+C для остановки после проверки.

## Шаг 7: Настройка Systemd

### 7.1 Скопируйте systemd service файл
```bash
cp /var/www/openrouterchats/deploy/systemd/openrouterchats.service /etc/systemd/system/
```



### 7.3 Запустите и включите сервис
```bash
systemctl daemon-reload
systemctl start openrouterchats
systemctl enable openrouterchats
```

### 7.4 Проверьте статус
```bash
systemctl status openrouterchats
```

### 7.5 Просмотр логов (при необходимости)
```bash
# Логи systemd
journalctl -u openrouterchats -f

# Логи Gunicorn
tail -f /var/log/gunicorn/error.log
tail -f /var/log/gunicorn/access.log
```

## Шаг 8: Настройка Nginx

### 8.1 Скопируйте конфигурацию Nginx
```bash
cp /var/www/openrouterchats/deploy/nginx/openrouterchats.conf /etc/nginx/sites-available/
```

### 8.2 Отредактируйте конфигурацию
```bash
nano /etc/nginx/sites-available/openrouterchats.conf
```
Замените `your_domain.com` на ваш реальный домен или IP адрес.

### 8.3 Создайте символическую ссылку
```bash
ln -s /etc/nginx/sites-available/openrouterchats.conf /etc/nginx/sites-enabled/
```

### 8.4 Удалите дефолтную конфигурацию (опционально)
```bash
rm /etc/nginx/sites-enabled/default
```

### 8.5 Проверьте конфигурацию Nginx
```bash
nginx -t
```

### 8.6 Перезапустите Nginx
```bash
systemctl restart nginx
systemctl enable nginx
```

## Шаг 9: Настройка Firewall

### 9.1 Настройте UFW (если используется)
```bash
ufw allow 'Nginx Full'
ufw allow OpenSSH
ufw enable
ufw status
```

## Шаг 10: Настройка SSL (рекомендуется)

### 10.1 Установите Certbot
```bash
apt install -y certbot python3-certbot-nginx
```

### 10.2 Получите SSL сертификат
```bash
certbot --nginx -d 151461.com/ -d www.151461.com/
```

### 10.3 Настройте автоматическое обновление
```bash
certbot renew --dry-run
```

После настройки SSL, раскомментируйте SSL блок в `/etc/nginx/sites-available/openrouterchats.conf` и перезапустите Nginx.

## Шаг 11: Проверка работы

### 11.1 Откройте браузер и перейдите на:
- HTTP: `http://your_domain.com` или `http://your_server_ip`
- HTTPS (после настройки SSL): `https://your_domain.com`

### 11.2 Проверьте админку Django:
- `https://your_domain.com/admin`

## Обслуживание и управление

### Перезапуск приложения
```bash
systemctl restart openrouterchats
```

### Обновление кода
```bash
cd /var/www/openrouterchats
git pull  # если используете Git
source venv/bin/activate
pip install -r requirements.txt
cd OpenRouterChats
python manage.py migrate
python manage.py collectstatic --noinput
systemctl restart openrouterchats
```

### Просмотр логов
```bash
# Логи приложения
journalctl -u openrouterchats -f

# Логи Nginx
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Логи Gunicorn
tail -f /var/log/gunicorn/access.log
tail -f /var/log/gunicorn/error.log
```

### Остановка/запуск сервисов
```bash
# Gunicorn (приложение)
systemctl stop openrouterchats
systemctl start openrouterchats
systemctl restart openrouterchats

# Nginx
systemctl stop nginx
systemctl start nginx
systemctl restart nginx
```

## Резервное копирование

### Создание бэкапа базы данных
```bash
cd /var/www/openrouterchats/OpenRouterChats
cp db.sqlite3 db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)
```

### Автоматический бэкап (добавьте в crontab)
```bash
crontab -e
```
Добавьте строку:
```
0 2 * * * cp /var/www/openrouterchats/OpenRouterChats/db.sqlite3 /var/www/openrouterchats/backups/db.sqlite3.$(date +\%Y\%m\%d)
```

## Решение проблем

### Проблема: 502 Bad Gateway
```bash
# Проверьте статус Gunicorn
systemctl status openrouterchats

# Проверьте логи
journalctl -u openrouterchats -n 50
```

### Проблема: Статические файлы не загружаются
```bash
# Пересоберите статику
cd /var/www/openrouterchats/OpenRouterChats
source /var/www/openrouterchats/venv/bin/activate
python manage.py collectstatic --noinput

# Проверьте права
chown -R www-data:www-data /var/www/openrouterchats/staticfiles
```

### Проблема: Permission denied
```bash
# Установите правильные права
chown -R www-data:www-data /var/www/openrouterchats
chmod -R 755 /var/www/openrouterchats
```

## Рекомендации по безопасности

1. ✅ Используйте сильный SECRET_KEY (уже настроено)
2. ✅ Отключите DEBUG в production (уже настроено)
3. ✅ Используйте HTTPS/SSL (настраивается в Шаге 10)
4. ✅ Настройте firewall (Шаг 9)
5. ✅ Регулярно обновляйте систему и зависимости
6. ✅ Делайте регулярные бэкапы базы данных
7. ✅ Не храните .env файл в Git репозитории
8. ✅ Используйте отдельного пользователя (www-data)

## Мониторинг производительности

### Установка htop для мониторинга
```bash
apt install -y htop
htop
```

### Мониторинг использования ресурсов
```bash
# Использование диска
df -h

# Использование памяти
free -h

# Процессы
ps aux | grep gunicorn
```

---

**Готово!** Ваше Django приложение теперь развернуто на production сервере.

Если возникнут проблемы, проверьте логи и убедитесь, что все шаги выполнены корректно.
