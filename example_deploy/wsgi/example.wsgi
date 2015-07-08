import os, sys
sys.path.append('/home/myuser/projects')
os.environ['DJANGO_SETTINGS_MODULE'] = 'example.settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
