"""
Identidad Visual y Constantes de Diseño - FarmaShield
Paleta de colores: Verde (#007167), Blanco Hueso (#D2C4B4) en fondo general
y Blanco Puro (#FFFFFF) para ticket de venta, paneles, tablas y tarjetas.
Centraliza estilos, fuentes, botones y Treeviews.
"""
import tkinter as tk
from tkinter import ttk

# ==============================================================================
# PALETA DE COLORES - FarmaShield
# ==============================================================================
COLOR_PRIMARY = "#007167"         # Verde principal FarmaShield
COLOR_PRIMARY_HOVER = "#005951"   # Verde más profundo para hover
COLOR_PRIMARY_ACTIVE = "#004740"  # Verde oscuro para acentos y cabeceras activas
COLOR_PRIMARY_LIGHT = "#E0F2F0"   # Verde menta muy claro para selecciones suaves

COLOR_BG = "#D2C4B4"              # Blanco hueso en fondo general
COLOR_PANEL = "#FFFFFF"           # Blanco puro para tarjetas, ticket de venta y paneles
COLOR_BORDER = "#B8A896"          # Blanco hueso acentuado para bordes elegantes
COLOR_BONE_LIGHT = "#EBE3DA"      # Blanco hueso suave para pestañas y fondos secundarios

COLOR_TEXT = "#232B2B"            # Texto principal oscuro de alta legibilidad
COLOR_TEXT_MUTED = "#5C6766"      # Texto secundario / gris verdoso sutil
COLOR_TEXT_WHITE = "#FFFFFF"      # Texto blanco sobre fondos verdes

# Colores Semánticos para Alertas de Caducidad y Estado
COLOR_SUCCESS = "#2E7D32"         # Verde para stock óptimo y pagos completados
COLOR_SUCCESS_BG = "#E8F5E9"
COLOR_WARNING = "#E65100"         # Naranja para lotes por vencer (<60 días)
COLOR_WARNING_BG = "#FFF3E0"
COLOR_DANGER = "#D32F2F"          # Rojo para lotes vencidos o errores
COLOR_DANGER_BG = "#FFEBEE"

# Tipografías recomendadas para Windows (Mantenidas como estaban)
FONT_TITLE_LARGE = ("Segoe UI", 20, "bold")
FONT_TITLE = ("Segoe UI", 15, "bold")
FONT_SUBTITLE = ("Segoe UI", 12, "bold")
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_REGULAR = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)
FONT_MONO = ("Consolas", 10)
FONT_MONO_BOLD = ("Consolas", 11, "bold")


def configure_styles(root: tk.Tk):
    """
    Configura y registra los estilos TTK en la aplicación principal.
    Aplica temas coherentes en botones, tablas (Treeview), pestañas y entradas.
    """
    style = ttk.Style(root)
    # Usar tema nativo 'clam' para permitir personalización completa de colores
    try:
        style.theme_use("clam")
    except Exception:
        pass

    # Configuración general
    style.configure(".", background=COLOR_BG, foreground=COLOR_TEXT, font=FONT_REGULAR)

    # 1. Frames y Paneles
    style.configure("Pink.TFrame", background=COLOR_BG)
    style.configure("Card.TFrame", background=COLOR_PANEL, relief="flat")
    style.configure("Bordered.TFrame", background=COLOR_PANEL, relief="solid", borderwidth=1, bordercolor=COLOR_BORDER)
    style.configure("Header.TFrame", background=COLOR_PRIMARY)

    # 2. Etiquetas (Labels)
    style.configure("TLabel", background=COLOR_BG, foreground=COLOR_TEXT, font=FONT_REGULAR)
    style.configure("Card.TLabel", background=COLOR_PANEL, foreground=COLOR_TEXT, font=FONT_REGULAR)
    style.configure("HeaderTitle.TLabel", background=COLOR_PRIMARY, foreground=COLOR_TEXT_WHITE, font=FONT_TITLE)
    style.configure("HeaderSubtitle.TLabel", background=COLOR_PRIMARY, foreground=COLOR_BG, font=FONT_SMALL)
    style.configure("Title.TLabel", background=COLOR_BG, foreground=COLOR_PRIMARY_ACTIVE, font=FONT_TITLE)
    style.configure("Subtitle.TLabel", background=COLOR_BG, foreground=COLOR_TEXT, font=FONT_SUBTITLE)
    style.configure("Muted.TLabel", background=COLOR_BG, foreground=COLOR_TEXT_MUTED, font=FONT_SMALL)
    style.configure("PinkMuted.TLabel", background=COLOR_PANEL, foreground=COLOR_PRIMARY, font=FONT_BOLD)

    # 3. Botones (Buttons con estilo verde FarmaShield)
    # Botón Principal Verde (mantiene alias Pink.TButton y Green.TButton)
    for btn_style in ["Pink.TButton", "Green.TButton", "Primary.TButton"]:
        style.configure(
            btn_style,
            background=COLOR_PRIMARY,
            foreground=COLOR_TEXT_WHITE,
            font=FONT_BOLD,
            borderwidth=0,
            focuscolor="none",
            padding=(14, 8)
        )
        style.map(
            btn_style,
            background=[("active", COLOR_PRIMARY_HOVER), ("pressed", COLOR_PRIMARY_ACTIVE), ("disabled", COLOR_BORDER)],
            foreground=[("disabled", "#8A9493")]
        )

    # Botón Secundario (Borde y fondo blanco puro o blanco hueso sutil)
    style.configure(
        "Secondary.TButton",
        background=COLOR_PANEL,
        foreground=COLOR_PRIMARY_ACTIVE,
        font=FONT_BOLD,
        borderwidth=1,
        bordercolor=COLOR_PRIMARY,
        focuscolor="none",
        padding=(12, 6)
    )
    style.map(
        "Secondary.TButton",
        background=[("active", COLOR_PRIMARY_LIGHT), ("pressed", COLOR_PRIMARY), ("disabled", "#EFEFEF")],
        foreground=[("active", COLOR_PRIMARY_ACTIVE), ("pressed", COLOR_TEXT_WHITE)]
    )

    # Botón de Cobro / Éxito (Verde FarmaShield Acento)
    style.configure(
        "Accent.TButton",
        background=COLOR_PRIMARY,
        foreground=COLOR_TEXT_WHITE,
        font=FONT_SUBTITLE,
        borderwidth=0,
        focuscolor="none",
        padding=(16, 10)
    )
    style.map(
        "Accent.TButton",
        background=[("active", COLOR_PRIMARY_HOVER), ("pressed", COLOR_PRIMARY_ACTIVE)]
    )

    # Botón de Peligro / Eliminar
    style.configure(
        "Danger.TButton",
        background=COLOR_DANGER_BG,
        foreground=COLOR_DANGER,
        font=FONT_BOLD,
        borderwidth=1,
        bordercolor=COLOR_DANGER,
        padding=(10, 5)
    )
    style.map(
        "Danger.TButton",
        background=[("active", COLOR_DANGER), ("pressed", "#B71C1C")],
        foreground=[("active", COLOR_TEXT_WHITE), ("pressed", COLOR_TEXT_WHITE)]
    )

    # 4. Entradas de Texto (Entry) - Blanco Puro
    style.configure(
        "TEntry",
        fieldbackground=COLOR_PANEL,
        foreground=COLOR_TEXT,
        bordercolor=COLOR_BORDER,
        lightcolor=COLOR_PRIMARY,
        darkcolor=COLOR_BORDER,
        padding=6,
        font=FONT_REGULAR
    )

    # 5. Treeview (Tablas en Blanco Puro con cabecera Verde FarmaShield)
    style.configure(
        "Treeview",
        background=COLOR_PANEL,
        foreground=COLOR_TEXT,
        fieldbackground=COLOR_PANEL,
        rowheight=28,
        font=FONT_REGULAR,
        bordercolor=COLOR_BORDER,
        borderwidth=1
    )
    style.map(
        "Treeview",
        background=[("selected", COLOR_PRIMARY_LIGHT)],
        foreground=[("selected", COLOR_PRIMARY_ACTIVE)]
    )

    style.configure(
        "Treeview.Heading",
        background=COLOR_PRIMARY,
        foreground=COLOR_TEXT_WHITE,
        font=FONT_BOLD,
        relief="flat",
        padding=6
    )
    style.map(
        "Treeview.Heading",
        background=[("active", COLOR_PRIMARY_HOVER)]
    )

    # 6. Notebook (Pestañas del panel de administración)
    style.configure(
        "TNotebook",
        background=COLOR_BG,
        borderwidth=0
    )
    style.configure(
        "TNotebook.Tab",
        background=COLOR_BONE_LIGHT,
        foreground=COLOR_TEXT,
        font=FONT_BOLD,
        padding=(16, 8),
        borderwidth=0
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", COLOR_PRIMARY), ("active", COLOR_BORDER)],
        foreground=[("selected", COLOR_TEXT_WHITE), ("active", COLOR_TEXT)]
    )

    # 7. Scrollbars
    style.configure(
        "Vertical.TScrollbar",
        background=COLOR_BONE_LIGHT,
        troughcolor=COLOR_BG,
        bordercolor=COLOR_BORDER,
        arrowcolor=COLOR_PRIMARY
    )
    style.configure(
        "Horizontal.TScrollbar",
        background=COLOR_BONE_LIGHT,
        troughcolor=COLOR_BG,
        bordercolor=COLOR_BORDER,
        arrowcolor=COLOR_PRIMARY
    )
