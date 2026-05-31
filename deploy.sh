#!/usr/bin/env bash
# =============================================================
# AkatsukiSoap — полный скрипт развёртывания на Ubuntu/Debian
# Запуск:  sudo bash deploy.sh
# =============================================================
set -euo pipefail

# ---- Настройки ------------------------------------------------
APP_NAME="akatsukisoap"
APP_DIR="/opt/${APP_NAME}"
APP_USER="www-data"
PYTHON_VERSION="python3"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"  # директория, откуда запущен скрипт

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[DEPLOY]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ---- Проверка root --------------------------------------------
if [[ $EUID -ne 0 ]]; then
    err "Запустите скрипт от root:  sudo bash deploy.sh"
fi

log "=== Начинаем развёртывание AkatsukiSoap ==="

# ---- 1. Системные пакеты --------------------------------------
log "1/9  Устанавливаем системные пакеты..."
apt-get update -qq
apt-get install -y -qq \
    ${PYTHON_VERSION} ${PYTHON_VERSION}-venv ${PYTHON_VERSION}-dev \
    python3-pip \
    nginx \
    build-essential \
    libffi-dev libssl-dev \
    pkg-config \
    libjpeg-dev zlib1g-dev \
    > /dev/null 2>&1

log "     Системные пакеты установлены."

# ---- 2. Копируем проект (если нужно) --------------------------
log "2/9  Подготавливаем директорию приложения..."
if [[ "${REPO_DIR}" != "${APP_DIR}" ]]; then
    mkdir -p "${APP_DIR}"
    rsync -a --exclude='venv' --exclude='.idea' --exclude='__pycache__' \
        --exclude='*.pyc' --exclude='db.sqlite3' \
        "${REPO_DIR}/" "${APP_DIR}/"
    log "     Проект скопирован в ${APP_DIR}"
else
    log "     Проект уже в ${APP_DIR}"
fi

# ---- 3. Файл .env --------------------------------------------
log "3/9  Проверяем .env..."
if [[ ! -f "${APP_DIR}/.env" ]]; then
    if [[ -f "${APP_DIR}/.env.example" ]]; then
        cp "${APP_DIR}/.env.example" "${APP_DIR}/.env"
        warn "     Создан ${APP_DIR}/.env из шаблона."
        warn "     ⚠  ОБЯЗАТЕЛЬНО отредактируйте .env перед первым запуском!"
    else
        err "     Нет .env и .env.example — не могу продолжить."
    fi
else
    log "     .env уже существует."
fi

# ---- 4. Виртуальное окружение и зависимости --------------------
log "4/9  Создаём виртуальное окружение и ставим зависимости..."
${PYTHON_VERSION} -m venv "${APP_DIR}/venv"
source "${APP_DIR}/venv/bin/activate"
pip install --upgrade pip setuptools wheel -q
pip install -r "${APP_DIR}/requirements.txt" -q
log "     Зависимости установлены."

# ---- 5. Django: миграции, статика, суперпользователь -----------
log "5/9  Применяем миграции и собираем статику..."
cd "${APP_DIR}"
python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear -v0

# Создаём суперпользователя, если его ещё нет
if ! python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); exit(0 if User.objects.filter(is_superuser=True).exists() else 1)" 2>/dev/null; then
    warn "     Суперпользователь не найден."
    warn "     Создайте его командой:  cd ${APP_DIR} && source venv/bin/activate && python manage.py createsuperuser"
fi
log "     Django подготовлен."

# ---- 6. Директории для логов -----------------------------------
log "6/9  Создаём директории для логов..."
mkdir -p /var/log/gunicorn
chown ${APP_USER}:${APP_USER} /var/log/gunicorn
mkdir -p "${APP_DIR}/media"
log "     Логи: /var/log/gunicorn/"

# ---- 7. Права --------------------------------------------------
log "7/9  Назначаем права..."
chown -R ${APP_USER}:${APP_USER} "${APP_DIR}"
chmod 600 "${APP_DIR}/.env"
log "     Права назначены."

# ---- 8. Systemd-юниты -----------------------------------------
log "8/9  Настраиваем systemd..."
cp "${APP_DIR}/systemd/akatsukisoap.service" /etc/systemd/system/
cp "${APP_DIR}/systemd/akatsukisoap-qcluster.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable ${APP_NAME}.service
systemctl enable ${APP_NAME}-qcluster.service
systemctl restart ${APP_NAME}.service
systemctl restart ${APP_NAME}-qcluster.service
log "     Gunicorn и Django-Q запущены."

# ---- 9. Nginx --------------------------------------------------
log "9/9  Настраиваем Nginx..."

# Извлекаем все хосты из DJANGO_ALLOWED_HOSTS и преобразуем запятые в пробелы для Nginx
ALLOWED_HOSTS_VAL=$(grep -oP 'DJANGO_ALLOWED_HOSTS=\K.+' "${APP_DIR}/.env" 2>/dev/null || echo "")
if [[ -n "${ALLOWED_HOSTS_VAL}" ]]; then
    DOMAIN=$(echo "${ALLOWED_HOSTS_VAL}" | tr ',' ' ')
else
    DOMAIN="YOUR_DOMAIN"
fi

# Копируем оригинальный шаблон во временный файл в sites-available
cp "${APP_DIR}/nginx/akatsukisoap.conf" "/etc/nginx/sites-available/${APP_NAME}"

# Подставляем домены/IP в скопированный конфиг Nginx (оригинальный шаблон остается нетронутым)
sed -i "s/YOUR_DOMAIN/${DOMAIN}/g" "/etc/nginx/sites-available/${APP_NAME}"

ln -sf /etc/nginx/sites-available/${APP_NAME} /etc/nginx/sites-enabled/${APP_NAME}

# Удаляем default, если мешает
rm -f /etc/nginx/sites-enabled/default

# Проверяем конфиг
nginx -t && systemctl reload nginx
log "     Nginx настроен."

# ---- Готово! ---------------------------------------------------
echo ""
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}   Развёртывание завершено!          ${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""
echo "  Проверьте статус:"
echo "    systemctl status ${APP_NAME}"
echo "    systemctl status ${APP_NAME}-qcluster"
echo ""
echo "  Логи Gunicorn:"
echo "    journalctl -u ${APP_NAME} -f"
echo "    tail -f /var/log/gunicorn/akatsukisoap-error.log"
echo ""
echo "  Для SSL (Let's Encrypt):"
echo "    apt install certbot python3-certbot-nginx"
echo "    certbot --nginx -d ${DOMAIN}"
echo ""
if [[ "${DOMAIN}" == "YOUR_DOMAIN" ]]; then
    echo -e "  ${YELLOW}⚠  Не забудьте:"
    echo -e "     1. Отредактировать ${APP_DIR}/.env"
    echo -e "     2. Перезапустить:  sudo bash ${APP_DIR}/deploy.sh${NC}"
fi
