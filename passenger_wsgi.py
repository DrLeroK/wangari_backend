# passenger_wsgi.py
import os
import sys

# 1) project root (folder that contains manage.py and the 'pld' package)
PROJECT_ROOT = '/home/pldassociationor/wangari_backend'
sys.path.insert(0, PROJECT_ROOT)
# also add inner package path if needed
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'wangari'))

# 2) try to activate the virtualenv created by cPanel (update path if different)
VENV_ACTIVATE = '/home/pldassociationor/virtualenv/wangari_backend/3.10/bin/activate_this.py'
SITE_PACKAGES = '/home/pldassociationor/virtualenv/wangari_backend/3.10/lib/python3.10/site-packages'

if os.path.exists(VENV_ACTIVATE):
    with open(VENV_ACTIVATE) as f:
        exec(f.read(), {'__file__': VENV_ACTIVATE})
else:
    # fallback: add site-packages if activate script not present
    sys.path.insert(0, SITE_PACKAGES)

# 3) tell Django which settings module to use
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wangari.settings.prod')

# 4) start the WSGI app
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()