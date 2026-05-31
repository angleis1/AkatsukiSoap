#!/usr/bin/env bash
# =============================================================
# AkatsukiSoap — быстрое обновление (после git pull)
# Запуск:  sudo bash update.sh
# =============================================================
set -euo pipefail

APP_DIR="/opt/akatsukisoap"
GREEN='\033[0;32m'
NC='\033[0m'

log() { echo -e "${GREEN}[UPDATE]${NC} $*"; }

if [[ $EUID -ne 0 ]]; then
    echo "Запустите от root:  sudo bash update.sh"
    exit 1
fi

cd "${APP_DIR}"
source venv/bin/activate

log "Устанавливаем зависимости..."
pip install -r requirements.txt -q

log "Применяем миграции..."
python manage.py migrate --noinput

log "Собираем статику..."
python manage.py collectstatic --noinput --clear -v0

log "Перезапускаем сервисы..."
systemctl restart akatsukisoap.service
systemctl restart akatsukisoap-qcluster.service
systemctl reload nginx

log "Готово! Сайт обновлён."
