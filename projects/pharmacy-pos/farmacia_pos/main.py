"""
Punto de Entrada Principal - Farmacia POS
Gestiona el ciclo de vida de la aplicación, inicializa la base de datos,
aplica la identidad visual en tonos rosas y evalúa el rol (RBAC) para abrir
la vista de Administrador o la vista de Caja / POS.
"""
import sys
import os
import argparse
import tkinter as tk
from tkinter import ttk, messagebox

# Asegurar que el directorio raíz del proyecto esté en sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from farmacia_pos.database.db import init_db, DB_ENV, get_active_connection_info
from farmacia_pos.services.auth_service import logout, get_current_user
from farmacia_pos.ui.styles import configure_styles, COLOR_BG
from farmacia_pos.ui.login_view import LoginView
from farmacia_pos.ui.pos_view import POSView
from farmacia_pos.ui.admin_view import AdminView


class MainApplication(tk.Tk):
    """Ventana principal que administra la navegación entre vistas según el rol RBAC."""

    def __init__(self, target_env: str = "test"):
        super().__init__()
        self.target_env = target_env
        self.title("FarmaShield - Sistema de Gestión Farmacéutica")
        self.geometry("1100x700")
        self.minsize(950, 600)
        self.configure(bg=COLOR_BG)

        # Configurar icono de la aplicación
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(base_dir, "assets", "icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
            else:
                png_path = os.path.join(base_dir, "assets", "logo_header.png")
                if os.path.exists(png_path):
                    self.iconphoto(False, tk.PhotoImage(file=png_path))
        except Exception:
            pass

        # Configurar estilos TTK con identidad visual FarmaShield (verde / blanco hueso)
        configure_styles(self)

        # Contenedor dinámico de vistas
        self.container = tk.Frame(self, bg=COLOR_BG)
        self.container.pack(fill="both", expand=True)

        self.current_view = None

        # Inicializar DB y arrancar con la vista de login
        self._init_database()
        self.show_login()

    def _init_database(self):
        """Inicializa la base de datos y crea las tablas si no existen."""
        try:
            print(f"[MAIN] Inicializando base de datos para entorno: '{self.target_env}'...")
            init_db(self.target_env)
        except Exception as e:
            print(f"[MAIN ERROR] Error al inicializar DB: {e}")
            messagebox.showwarning(
                "Aviso de Base de Datos",
                f"No se pudo conectar de inmediato con el servidor configurado ({e}).\n"
                "El sistema iniciará en modo local seguro de pruebas.",
                parent=self
            )

    def _clear_container(self):
        """Limpia los widgets hijos del contenedor principal."""
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_login(self):
        """Muestra la pantalla de acceso."""
        logout()
        self._clear_container()
        self.current_view = LoginView(self.container, on_login_success=self.handle_login_success)
        self.current_view.pack(fill="both", expand=True)

    def handle_login_success(self, user):
        """
        Pilar 2: Control de Acceso Basado en Roles (RBAC).
        Evalúa el rol del usuario ('admin' o 'empleado') para desplegar
        la ventana correspondiente.
        """
        rol_nombre = user.rol.nombre.lower() if (user and user.rol) else "empleado"

        if rol_nombre == "admin":
            # Administrador: Abre panel de control completo
            self.show_admin()
        else:
            # Empleado / Cajero: Abre vista restringida de ventas
            self.show_pos()

    def show_pos(self):
        """Muestra la vista de ventas / caja."""
        self._clear_container()
        self.current_view = POSView(
            self.container,
            on_logout=self.show_login,
            on_open_admin=self.show_admin
        )
        self.current_view.pack(fill="both", expand=True)

    def show_admin(self):
        """Muestra el panel de administración."""
        self._clear_container()
        self.current_view = AdminView(
            self.container,
            on_logout=self.show_login,
            on_open_pos=self.show_pos
        )
        self.current_view.pack(fill="both", expand=True)


def main():
    parser = argparse.ArgumentParser(description="Farmacia POS - Sistema de Punto de Venta")
    parser.add_argument(
        "--env",
        choices=["test", "prod"],
        default=os.getenv("FARMACIA_ENV", "test").lower(),
        help="Entorno de base de datos: 'test' (MySQL Workbench local) o 'prod' (SQL Server original)"
    )
    args = parser.parse_args()

    app = MainApplication(target_env=args.env)
    app.mainloop()


if __name__ == "__main__":
    main()
