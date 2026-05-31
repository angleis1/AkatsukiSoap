# Gunicorn configuration for AkatsukiSoap
# https://docs.gunicorn.org/en/stable/settings.html

import multiprocessing

# Привязка
bind = "127.0.0.1:8000"

# Воркеры: (2 × ядра) + 1
workers = multiprocessing.cpu_count() * 2 + 1

# Таймаут (сек)
timeout = 120

# Перезапуск воркеров после N запросов (защита от утечек памяти)
max_requests = 1000
max_requests_jitter = 50

# Логирование
accesslog = "/var/log/gunicorn/akatsukisoap-access.log"
errorlog = "/var/log/gunicorn/akatsukisoap-error.log"
loglevel = "info"

# WSGI-приложение
wsgi_app = "soap_site.wsgi:application"
