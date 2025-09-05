# routes/__init__.py
from . import auth
from . import admin

# Only include modules that actually exist
__all__ = ['auth', 'admin']