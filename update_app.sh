#!/bin/bash

# Скрипт для удаленного обновления Django приложения OpenRouterChats
# Подключается к серверу 94.154.11.231 под пользователем root

set -e  # Выход при любой ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Параметры
REMOTE_HOST="94.154.11.231"
REMOTE_USER="root"
REMOTE_PORT="22"
APP_DIR="/var/www/openrouterchats"
VENV_DIR="$APP_DIR/venv"
PROJECT_DIR="$APP_DIR/OpenRouterChats"
SERVICE_NAME="openrouterchats"
UPDATE_REQUIREMENTS=false

# Функция для вывода цветных сообщений
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Функция для проверки успешности команды
check_command() {
    if [ $? -eq 0 ]; then
        log_info "$1 выполнено успешно"
    else
        log_error "$1 выполнено с ошибкой"
        exit 1
    fi
}

# Функция удаленного обновления через SSH
update_remote() {
    log_info "Начало удаленного обновления на $REMOTE_USER@$REMOTE_HOST..."
    
    # Создание временного скрипта на удаленном сервере
    ssh -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" "cat > /tmp/update_openrouterchats.sh" << EOF
#!/bin/bash

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

APP_DIR="$APP_DIR"
VENV_DIR="$VENV_DIR"
PROJECT_DIR="$PROJECT_DIR"
SERVICE_NAME="$SERVICE_NAME"
UPDATE_REQUIREMENTS=$UPDATE_REQUIREMENTS

log_info() {
    echo -e "\${GREEN}[INFO]\${NC} \$1"
}

log_warn() {
    echo -e "\${YELLOW}[WARN]\${NC} \$1"
}

log_error() {
    echo -e "\${RED}[ERROR]\${NC} \$1"
}

check_command() {
    if [ \$? -eq 0 ]; then
        log_info "\$1 выполнено успешно"
    else
        log_error "\$1 выполнено с ошибкой"
        exit 1
    fi
}

log_info "Начало обновления на удаленном сервере..."

# Проверка существования директории
if [ ! -d "\$APP_DIR" ]; then
    log_error "Директория \$APP_DIR не существует"
    exit 1
fi

# Переход в директорию приложения
cd "\$APP_DIR"

# Обновление кода из Git
log_info "Обновление кода из Git..."
git pull
check_command "Git pull"

# Активация виртуального окружения
if [ -d "\$VENV_DIR" ]; then
    log_info "Активация виртуального окружения..."
    source "\$VENV_DIR/bin/activate"
else
    log_warn "Виртуальное окружение не найдено, продолжаем без него"
fi

# Обновление зависимостей (если указан флаг --req)
if [ "\$UPDATE_REQUIREMENTS" = true ]; then
    log_info "Обновление зависимостей..."
    pip install -r requirements.txt
    check_command "Установка зависимостей"
else
    log_warn "Обновление зависимостей пропущено (используйте флаг --req)"
fi

# Переход в директорию проекта
cd "\$PROJECT_DIR"

# Применение миграций
log_info "Применение миграций базы данных..."
python manage.py migrate
check_command "Миграции базы данных"

# Сбор статических файлов
log_info "Сбор статических файлов..."
python manage.py collectstatic --noinput
check_command "Сбор статики"

# Перезапуск сервиса
log_info "Перезапуск сервиса \$SERVICE_NAME..."
systemctl restart "\$SERVICE_NAME"
check_command "Перезапуск сервиса"

# Проверка статуса сервиса
log_info "Проверка статуса сервиса..."
systemctl status "\$SERVICE_NAME" --no-pager

log_info "Удаленное обновление завершено успешно!"

# Удаление временного скрипта
rm -f "\$0"
EOF
    
    # Сделать скрипт исполняемым и запустить его
    ssh -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" "chmod +x /tmp/update_openrouterchats.sh && /tmp/update_openrouterchats.sh"
    
    if [ $? -eq 0 ]; then
        log_info "Удаленное обновление выполнено успешно!"
    else
        log_error "Ошибка при выполнении удаленного обновления"
        exit 1
    fi
}

# Функция вывода помощи
show_help() {
    echo "Скрипт удаленного обновления Django приложения OpenRouterChats"
    echo ""
    echo "Использование:"
    echo "  $0 [опции]"
    echo ""
    echo "Опции:"
    echo "  --req                          Обновить зависимости из requirements.txt"
    echo "  --help                         Показать эту справку"
    echo ""
    echo "Сервер: $REMOTE_USER@$REMOTE_HOST:$REMOTE_PORT"
    echo "Директория приложения: $APP_DIR"
    echo ""
    echo "Примеры:"
    echo "  $0                             # Обновление без установки зависимостей"
    echo "  $0 --req                       # Обновление с установкой зависимостей"
}

# Парсинг аргументов командной строки
while [[ $# -gt 0 ]]; do
    case $1 in
        --req)
            UPDATE_REQUIREMENTS=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            log_error "Неизвестная опция: $1"
            show_help
            exit 1
            ;;
    esac
done

# Запуск удаленного обновления
update_remote
