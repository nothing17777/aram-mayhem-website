import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loltracker.settings')
application = get_wsgi_application()

# Render defaults to looking for 'app:app' for Gunicorn.
# Mapping the Django WSGI application to 'app' here.
app = application
