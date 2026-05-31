import os, sys

# Активация виртуального окружения
activate_this = '/home/username/python/bin/activate_this.py'
with open(activate_this) as f:
    exec(f.read(), {'__file__': activate_this})

# Добавляем путь к вашему проекту
sys.path.insert(0, os.path.join('/home/username/domains/domain.ru/myproject'))

# Указываем настройки Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'myproject.settings'

# Запускаем приложение
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()