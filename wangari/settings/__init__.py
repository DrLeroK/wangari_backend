# wangari/settings/__init__.py
# from .dev import *  # use this in development
# from .prod import *  # use this in production

import os

env = os.getenv('DJANGO_ENV', 'dev')

if env == 'prod':
    from .prod import *
else:
    from .dev import *