"""
Pantalla de Inicio de Sesión (Login) - FarmaShield
Pilar 2: Control de Acceso Basado en Roles (RBAC), identidad visual verde/blanco hueso
y selector de sucursal para gestión de stocks independientes.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable
from PIL import Image, ImageTk

from .styles import (
    COLOR_BG, COLOR_PANEL, COLOR_PRIMARY, COLOR_PRIMARY_HOVER,
    COLOR_PRIMARY_ACTIVE, COLOR_BORDER, COLOR_TEXT,
    COLOR_TEXT_MUTED, COLOR_TEXT_WHITE, COLOR_DANGER, FONT_TITLE_LARGE,
    FONT_TITLE, FONT_SUBTITLE, FONT_BOLD, FONT_REGULAR, FONT_SMALL
)
from ..services.auth_service import login
from ..services.inventory_service import list_branches
from ..database.db import get_active_connection_info


class LoginView(tk.Frame):
    """
    Vista de autenticación de usuarios de FarmaShield.
    Permite al usuario ingresar manualmente sus credenciales,
    seleccionar sucursal de operación, y transfiere el control
    al callback on_login_success(user) según el rol RBAC.
    """

    def __init__(self, parent: tk.Tk or tk.Frame, on_login_success: Callable):
        super().__init__(parent, bg=COLOR_BG)
        self.parent = parent
        self.on_login_success = on_login_success
        self.show_password = False
        self.branch_map = {}
        self.logo_img = None

        self._load_logo()
        self._build_ui()

    def _load_logo(self):
        """Carga el logo oficial de FarmaShield desde assets."""
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            logo_path = os.path.join(base_dir, "assets", "logo_login.png")
            if os.path.exists(logo_path):
                pil_img = Image.open(logo_path)
                self.logo_img = ImageTk.PhotoImage(pil_img)
        except Exception as e:
            print(f"[LOGIN] No se pudo cargar imagen de logo: {e}")
            self.logo_img = None

    def _build_ui(self):
        center_container = tk.Frame(self, bg=COLOR_BG)
        center_container.place(relx=0.5, rely=0.5, anchor="center")

        # Tarjeta de Login en Blanco Puro (#FFFFFF) con borde blanco hueso
        card = tk.Frame(
            center_container,
            bg=COLOR_PANEL,
            padx=42,
            pady=32,
            relief="solid",
            borderwidth=1,
            highlightbackground=COLOR_BORDER,
            highlightthickness=1
        )
        card.pack()

        # Logo FarmaShield
        if self.logo_img:
            lbl_logo = tk.Label(card, image=self.logo_img, bg=COLOR_PANEL)
            lbl_logo.pack(pady=(0, 6))
        else:
            icon_label = tk.Label(
                card,
                text="🛡️ ⚕️",
                font=("Segoe UI", 34),
                bg=COLOR_PANEL,
                fg=COLOR_PRIMARY
            )
            icon_label.pack(pady=(0, 4))

        lbl_title = tk.Label(
            card,
            text="FarmaShield",
            font=FONT_TITLE_LARGE,
            bg=COLOR_PANEL,
            fg=COLOR_PRIMARY_ACTIVE
        )
        lbl_title.pack()

        lbl_subtitle = tk.Label(
            card,
            text="Sistema de Gestión Multi-Sucursal",
            font=FONT_SMALL,
            bg=COLOR_PANEL,
            fg=COLOR_TEXT_MUTED
        )
        lbl_subtitle.pack(pady=(0, 14))

        divider = tk.Frame(card, bg=COLOR_BORDER, height=1, width=320)
        divider.pack(pady=(0, 14))

        self.lbl_msg = tk.Label(
            card,
            text="",
            font=FONT_SMALL,
            bg=COLOR_PANEL,
            fg=COLOR_DANGER,
            wraplength=320
        )
        self.lbl_msg.pack(pady=(0, 6))

        form_frame = tk.Frame(card, bg=COLOR_PANEL)
        form_frame.pack(fill="x")

        # Campo: Sucursal de Operación
        lbl_suc = tk.Label(
            form_frame,
            text="🏪 Sucursal de Operación:",
            font=FONT_BOLD,
            bg=COLOR_PANEL,
            fg=COLOR_PRIMARY_ACTIVE
        )
        lbl_suc.pack(anchor="w", pady=(0, 4))

        # Cargar sucursales de la BD
        sucursales = list_branches(only_active=True)
        self.branch_map = {s["nombre"]: s["id"] for s in sucursales}
        branch_names = list(self.branch_map.keys()) if self.branch_map else ["Farmacia Central"]

        self.combo_sucursal = ttk.Combobox(
            form_frame,
            values=branch_names,
            state="readonly",
            font=FONT_REGULAR,
            width=28
        )
        if branch_names:
            self.combo_sucursal.current(0)
        self.combo_sucursal.pack(fill="x", ipady=3, pady=(0, 12))

        # Campo: Usuario
        lbl_user = tk.Label(
            form_frame,
            text="Nombre de Usuario",
            font=FONT_BOLD,
            bg=COLOR_PANEL,
            fg=COLOR_TEXT
        )
        lbl_user.pack(anchor="w", pady=(0, 4))

        self.entry_user = ttk.Entry(form_frame, font=FONT_REGULAR, width=30)
        self.entry_user.pack(fill="x", ipady=3, pady=(0, 12))
        self.entry_user.focus_set()

        # Campo: Contraseña
        lbl_pass = tk.Label(
            form_frame,
            text="Contraseña",
            font=FONT_BOLD,
            bg=COLOR_PANEL,
            fg=COLOR_TEXT
        )
        lbl_pass.pack(anchor="w", pady=(0, 4))

        pass_container = tk.Frame(form_frame, bg=COLOR_PANEL)
        pass_container.pack(fill="x", pady=(0, 18))

        self.entry_pass = ttk.Entry(pass_container, font=FONT_REGULAR, show="•", width=26)
        self.entry_pass.pack(side="left", fill="x", expand=True, ipady=3)

        self.btn_eye = tk.Button(
            pass_container,
            text="👁️",
            font=("Segoe UI", 9),
            bg=COLOR_PANEL,
            fg=COLOR_PRIMARY,
            relief="solid",
            borderwidth=1,
            cursor="hand2",
            command=self._toggle_password_visibility
        )
        self.btn_eye.pack(side="right", padx=(5, 0), ipady=2)

        # Botón Ingresar Principal (Verde FarmaShield)
        self.btn_login = ttk.Button(
            card,
            text="INGRESAR AL SISTEMA",
            style="Primary.TButton",
            command=self._handle_login
        )
        self.btn_login.pack(fill="x", pady=(0, 10), ipady=4)

        # Botón / Enlace: Si se olvida contraseña solicitar al administrador
        btn_forgot = tk.Button(
            card,
            text="¿Olvidó su contraseña? Solicite al administrador",
            font=FONT_SMALL,
            bg=COLOR_PANEL,
            fg=COLOR_PRIMARY,
            activebackground=COLOR_PANEL,
            activeforeground=COLOR_PRIMARY_ACTIVE,
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self._show_forgot_password_info
        )
        btn_forgot.pack(pady=(2, 10))

        # Enlace tecla Enter
        self.entry_user.bind("<Return>", lambda e: self.entry_pass.focus_set())
        self.entry_pass.bind("<Return>", lambda e: self._handle_login())

        # Pie de conexión
        conn_info = get_active_connection_info()
        status_text = f"🔌 Conectado: {conn_info.get('name', 'DB')} | Servidor: {conn_info.get('server', 'localhost')}"
        if conn_info.get("is_fallback"):
            status_text += " [Modo Local]"

        lbl_status = tk.Label(
            card,
            text=status_text,
            font=("Segoe UI", 8),
            bg=COLOR_PANEL,
            fg=COLOR_TEXT_MUTED,
            wraplength=320
        )
        lbl_status.pack(pady=(4, 0))

    def _show_forgot_password_info(self):
        """Muestra ventana indicando que debe solicitar el cambio al administrador."""
        messagebox.showinfo(
            "Recuperación de Contraseña - FarmaShield",
            "Por políticas de seguridad del sistema,\n"
            "si ha olvidado su contraseña, por favor solicite el\n"
            "restablecimiento directamente al Administrador.",
            parent=self
        )

    def _toggle_password_visibility(self):
        self.show_password = not self.show_password
        if self.show_password:
            self.entry_pass.configure(show="")
            self.btn_eye.configure(text="🔒")
        else:
            self.entry_pass.configure(show="•")
            self.btn_eye.configure(text="👁️")

    def _handle_login(self):
        u = self.entry_user.get().strip()
        p = self.entry_pass.get()

        selected_suc_name = self.combo_sucursal.get()
        sucursal_id = self.branch_map.get(selected_suc_name, 1)

        self.lbl_msg.configure(text="Verificando credenciales y sucursal...", fg=COLOR_PRIMARY)
        self.update_idletasks()

        success, user, message = login(u, p, sucursal_id=sucursal_id)
        if success and user:
            self.lbl_msg.configure(text="")
            self.on_login_success(user)
        else:
            self.lbl_msg.configure(text=f"⚠️ {message}", fg=COLOR_DANGER)
            self.entry_pass.delete(0, tk.END)
            self.entry_pass.focus_set()
