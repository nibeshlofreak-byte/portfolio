"""
Módulo de Interfaz de Usuario (UI) - Farmacia POS
Vistas en tonos rosas: Login, Administrador y Punto de Venta (Caja).
"""
from .styles import configure_styles
from .login_view import LoginView
from .pos_view import POSView
from .admin_view import AdminView

__all__ = ["configure_styles", "LoginView", "POSView", "AdminView"]
