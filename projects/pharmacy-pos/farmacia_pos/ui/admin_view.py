"""
Panel de Control del Administrador (Admin) - Farmacia POS
KPIs, Gráficos Interactivos (Matplotlib), Filtros por Fecha y Sucursal,
Semáforo FEFO, Gestión Multi-Sucursal, Catálogo y Usuarios RBAC.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional, Dict, Any, List
from datetime import datetime, date
from PIL import Image, ImageTk

# Integración de Matplotlib con Tkinter
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .styles import (
    COLOR_BG, COLOR_PANEL, COLOR_PRIMARY, COLOR_PRIMARY_HOVER,
    COLOR_PRIMARY_ACTIVE, COLOR_PRIMARY_LIGHT, COLOR_BORDER, COLOR_TEXT,
    COLOR_TEXT_MUTED, COLOR_TEXT_WHITE, COLOR_SUCCESS, COLOR_WARNING,
    COLOR_DANGER, FONT_TITLE, FONT_TITLE_LARGE, FONT_SUBTITLE, FONT_BOLD,
    FONT_REGULAR, FONT_SMALL
)
from ..services.inventory_service import (
    get_all_products_with_stock,
    check_batch_expirations,
    create_product,
    create_batch,
    get_inventory_statistics,
    list_branches,
    create_branch
)
from ..services.auth_service import (
    list_users,
    create_user,
    toggle_user_status,
    list_roles,
    get_current_user
)
from ..services.sales_service import (
    get_sales_history,
    get_sale_details
)
from ..services.analytics_service import (
    get_kpis_and_metrics,
    get_temporal_sales_trend,
    get_top_selling_products,
    get_payment_methods_distribution,
    get_sales_by_branch_comparison
)
from ..utils.printer import show_ticket_modal


class AdminView(tk.Frame):
    """
    Panel Administrativo integral con analítica avanzada, KPIs,
    gráficos interactivos en tonos rosas, filtros dinámicos y multi-sucursal.
    """

    def __init__(self, parent: tk.Tk or tk.Frame, on_logout: Callable, on_open_pos: Optional[Callable] = None):
        super().__init__(parent, bg=COLOR_BG)
        self.parent = parent
        self.on_logout = on_logout
        self.on_open_pos = on_open_pos

        self.branch_filter_map = {}
        self.chart_canvas = None
        self.logo_img = None

        self._load_logo()
        self._build_ui()
        self._refresh_all_data()

    def _load_logo(self):
        """Carga el logo FarmaShield para la barra de administración."""
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            logo_path = os.path.join(base_dir, "assets", "logo_header.png")
            if os.path.exists(logo_path):
                pil_img = Image.open(logo_path)
                self.logo_img = ImageTk.PhotoImage(pil_img)
        except Exception as e:
            print(f"[ADMIN] No se pudo cargar logo: {e}")
            self.logo_img = None

    def _build_ui(self):
        # 1. HEADER ADMINISTRATIVO VERDE FARMASHIELD
        header = tk.Frame(self, bg=COLOR_PRIMARY_ACTIVE, padx=20, pady=10)
        header.pack(fill="x")

        left_h = tk.Frame(header, bg=COLOR_PRIMARY_ACTIVE)
        left_h.pack(side="left")

        if self.logo_img:
            lbl_logo = tk.Label(left_h, image=self.logo_img, bg=COLOR_PRIMARY_ACTIVE)
            lbl_logo.pack(side="left", padx=(0, 10))

        lbl_title = tk.Label(
            left_h,
            text="FarmaShield - Panel Administrativo",
            font=FONT_TITLE,
            bg=COLOR_PRIMARY_ACTIVE,
            fg=COLOR_TEXT_WHITE
        )
        lbl_title.pack(side="left")

        right_h = tk.Frame(header, bg=COLOR_PRIMARY_ACTIVE)
        right_h.pack(side="right")

        user = get_current_user()

        # Botón de tres puntitos con menú desplegable
        menu_btn = tk.Menubutton(
            right_h,
            text="⋮",
            font=("Segoe UI", 16, "bold"),
            bg=COLOR_PRIMARY_ACTIVE,
            fg=COLOR_TEXT_WHITE,
            activebackground=COLOR_PRIMARY_HOVER,
            activeforeground=COLOR_TEXT_WHITE,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=8,
            pady=0
        )
        options_menu = tk.Menu(menu_btn, tearoff=0, font=FONT_REGULAR, bg=COLOR_PANEL, fg=COLOR_TEXT, activebackground=COLOR_PRIMARY_LIGHT, activeforeground=COLOR_PRIMARY_ACTIVE)
        if self.on_open_pos:
            options_menu.add_command(label="🛒 Abrir Caja / POS", command=self.on_open_pos)
            options_menu.add_separator()
        options_menu.add_command(label="🚪 Cerrar Sesión", command=self.on_logout)
        menu_btn.config(menu=options_menu)
        menu_btn.pack(side="right", padx=(5, 0))

        # 2. CUERPO CON PESTAÑAS (NOTEBOOK)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=10)

        self.tab_analytics = tk.Frame(self.notebook, bg=COLOR_BG)
        self.tab_semaforo = tk.Frame(self.notebook, bg=COLOR_BG)
        self.tab_inventory = tk.Frame(self.notebook, bg=COLOR_BG)
        self.tab_branches = tk.Frame(self.notebook, bg=COLOR_BG)
        self.tab_users = tk.Frame(self.notebook, bg=COLOR_BG)
        self.tab_sales = tk.Frame(self.notebook, bg=COLOR_BG)

        self.notebook.add(self.tab_analytics, text="Graficos de control")
        self.notebook.add(self.tab_semaforo, text="vencimientos/stock")
        self.notebook.add(self.tab_inventory, text="medicamentos y lotes")
        self.notebook.add(self.tab_branches, text="sucursales")
        self.notebook.add(self.tab_users, text="usuarios")
        self.notebook.add(self.tab_sales, text="Reporte de Ventas")

        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self._on_tab_changed())

        # Construir contenido de cada pestaña
        self._build_tab_analytics()
        self._build_tab_semaforo()
        self._build_tab_inventory()
        self._build_tab_branches()
        self._build_tab_users()
        self._build_tab_sales()

    # =========================================================================
    # TAB 1: KPIS Y GRÁFICOS INTERACTIVOS (MATPLOTLIB)
    # =========================================================================
    def _build_tab_analytics(self):
        frame = self.tab_analytics

        # A. Barra de Filtros Interactiva
        filter_bar = tk.Frame(
            frame,
            bg=COLOR_PANEL,
            padx=14,
            pady=10,
            relief="solid",
            borderwidth=1,
            highlightbackground=COLOR_BORDER,
            highlightthickness=1
        )
        filter_bar.pack(fill="x", pady=(8, 10))

        tk.Label(filter_bar, text="🔍 FILTROS:", font=FONT_BOLD, bg=COLOR_PANEL, fg=COLOR_PRIMARY_ACTIVE).pack(side="left", padx=(0, 10))

        # Filtro Sucursal
        tk.Label(filter_bar, text="Sucursal:", font=FONT_REGULAR, bg=COLOR_PANEL, fg=COLOR_TEXT).pack(side="left", padx=(0, 5))
        self.combo_filter_sucursal = ttk.Combobox(filter_bar, state="readonly", width=22)
        self.combo_filter_sucursal.pack(side="left", padx=(0, 15))

        # Filtro Período
        tk.Label(filter_bar, text="Período:", font=FONT_REGULAR, bg=COLOR_PANEL, fg=COLOR_TEXT).pack(side="left", padx=(0, 5))
        self.combo_filter_periodo = ttk.Combobox(
            filter_bar,
            values=["Este Mes", "Hoy", "Últimos 7 Días", "Últimos 30 Días", "Historial Completo"],
            state="readonly",
            width=18
        )
        self.combo_filter_periodo.set("Este Mes")
        self.combo_filter_periodo.pack(side="left", padx=(0, 15))

        btn_apply_filter = ttk.Button(
            filter_bar,
            text="⚡ Aplicar Filtros",
            style="Pink.TButton",
            command=self._load_analytics_tab
        )
        btn_apply_filter.pack(side="left", padx=5)

        # B. Tarjetas de KPIs Superiores
        kpi_container = tk.Frame(frame, bg=COLOR_BG)
        kpi_container.pack(fill="x", pady=(0, 10))

        def make_kpi_card(parent, title, val_text, color_accent):
            card = tk.Frame(
                parent,
                bg=COLOR_PANEL,
                padx=12,
                pady=10,
                relief="solid",
                borderwidth=1,
                highlightbackground=COLOR_BORDER,
                highlightthickness=1
            )
            card.pack(side="left", fill="both", expand=True, padx=4)

            tk.Label(card, text=title, font=("Segoe UI", 9), bg=COLOR_PANEL, fg=COLOR_TEXT_MUTED).pack(anchor="w")
            lbl_val = tk.Label(card, text=val_text, font=FONT_TITLE, bg=COLOR_PANEL, fg=color_accent)
            lbl_val.pack(anchor="w", pady=(2, 0))
            return lbl_val

        self.kpi_ventas_dia = make_kpi_card(kpi_container, "💵 Ventas del Día", "$0.00", COLOR_PRIMARY_ACTIVE)
        self.kpi_ventas_mes = make_kpi_card(kpi_container, "📅 Ventas del Mes", "$0.00", COLOR_PRIMARY)
        self.kpi_ticket_prom = make_kpi_card(kpi_container, "🎟️ Ticket Promedio", "$0.00", COLOR_SUCCESS)
        self.kpi_ingresos_filtro = make_kpi_card(kpi_container, "💰 Ingresos en Período", "$0.00", COLOR_PRIMARY_ACTIVE)
        self.kpi_transacciones = make_kpi_card(kpi_container, "🛒 Transacciones", "0", COLOR_TEXT)

        # C. Contenedor de Gráficos con Matplotlib
        self.charts_frame = tk.Frame(frame, bg=COLOR_PANEL, relief="solid", borderwidth=1, highlightbackground=COLOR_BORDER, highlightthickness=1)
        self.charts_frame.pack(fill="both", expand=True, pady=(0, 5))

    def _render_matplotlib_charts(self, sucursal_id: Optional[int], date_preset: str):
        """
        Dibuja los 4 gráficos interactivos de control con la paleta FarmaShield (#007167, blanco puro):
        1. Curva de Tendencia Temporal (Ventas diarias)
        2. Gráfico de Barras (Top Medicamentos más vendidos)
        3. Gráfico Circular / Donut (Métodos de Pago más usados)
        4. Comparativa de Rendimiento entre Sucursales
        """
        for w in self.charts_frame.winfo_children():
            w.destroy()

        # Crear Figura Matplotlib 2x2
        fig = Figure(figsize=(10, 4.8), dpi=95, facecolor="#FFFFFF")
        fig.subplots_adjust(left=0.07, right=0.96, top=0.91, bottom=0.12, wspace=0.32, hspace=0.45)

        # Paleta de colores para los gráficos FarmaShield
        color_primary_green = "#007167"
        color_dark_green = "#004740"
        color_light_green = "#E0F2F0"
        color_border = "#B8A896"
        color_accent_green = "#0E8A7D"
        color_palette_pie = ["#007167", "#004740", "#0E8A7D", "#4DAFA5", "#7BC7BF"]

        # --- 1. Gráfico 1: Curva de Tendencia Temporal ---
        ax1 = fig.add_subplot(2, 2, 1)
        ax1.set_facecolor("#FFFFFF")
        trend_dates, trend_values = get_temporal_sales_trend(sucursal_id=sucursal_id, days=12)

        ax1.plot(trend_dates, trend_values, marker="o", color=color_primary_green, linewidth=2.5, markersize=5, label="Ventas ($)")
        ax1.fill_between(trend_dates, trend_values, color=color_light_green, alpha=0.6)
        ax1.set_title("Curva de Tendencia Temporal (Ventas Diarias)", fontsize=10, fontweight="bold", color=color_dark_green, pad=8)
        ax1.grid(True, linestyle="--", alpha=0.4, color=color_border)
        ax1.tick_params(axis="x", rotation=30, labelsize=8)
        ax1.tick_params(axis="y", labelsize=8)

        # --- 2. Gráfico 2: Top Medicamentos Más Vendidos ---
        ax2 = fig.add_subplot(2, 2, 2)
        ax2.set_facecolor("#FFFFFF")
        top_names, top_quantities = get_top_selling_products(sucursal_id=sucursal_id, date_preset=date_preset, limit=5)

        if top_names:
            y_pos = range(len(top_names))
            bars = ax2.barh(y_pos, top_quantities, color=color_primary_green, height=0.55, edgecolor=color_dark_green)
            ax2.set_yticks(y_pos)
            ax2.set_yticklabels(top_names, fontsize=8)
            ax2.invert_yaxis()
            ax2.bar_label(bars, padding=3, fontsize=8, color=color_dark_green)
        else:
            ax2.text(0.5, 0.5, "Sin ventas en este período", ha="center", va="center", color=COLOR_TEXT_MUTED, fontsize=9)

        ax2.set_title("Top Medicamentos Más Vendidos", fontsize=10, fontweight="bold", color=color_dark_green, pad=8)
        ax2.grid(axis="x", linestyle="--", alpha=0.3, color=color_border)
        ax2.tick_params(axis="x", labelsize=8)

        # --- 3. Gráfico 3: Gráfico Circular / Donut (Métodos de Pago) ---
        ax3 = fig.add_subplot(2, 2, 3)
        ax3.set_facecolor("#FFFFFF")
        metodos, montos, conteos = get_payment_methods_distribution(sucursal_id=sucursal_id, date_preset=date_preset)

        if montos and sum(montos) > 0:
            wedges, texts, autotexts = ax3.pie(
                montos,
                labels=metodos,
                autopct="%1.1f%%",
                startangle=140,
                colors=color_palette_pie[:len(montos)],
                textprops={"fontsize": 8},
                wedgeprops=dict(width=0.6, edgecolor="#FFFFFF")  # Donut
            )
            for autotext in autotexts:
                autotext.set_color("#FFFFFF")
                autotext.set_fontweight("bold")
                autotext.set_fontsize(7.5)
        else:
            ax3.text(0.5, 0.5, "Sin transacciones registradas", ha="center", va="center", color=COLOR_TEXT_MUTED, fontsize=9)

        ax3.set_title("Métodos de Pago Más Usados", fontsize=10, fontweight="bold", color=color_dark_green, pad=8)

        # --- 4. Gráfico 4: Comparativa de Ventas por Sucursal ---
        ax4 = fig.add_subplot(2, 2, 4)
        ax4.set_facecolor("#FFFFFF")
        suc_names, suc_totals = get_sales_by_branch_comparison(date_preset=date_preset)

        if suc_names:
            x_pos = range(len(suc_names))
            bars_suc = ax4.bar(x_pos, suc_totals, color=color_primary_green, width=0.45, edgecolor=color_dark_green)
            ax4.set_xticks(x_pos)
            short_suc_names = [s.replace("Sucursal ", "") for s in suc_names]
            ax4.set_xticklabels(short_suc_names, fontsize=8, rotation=15)
            ax4.bar_label(bars_suc, fmt="$%.0f", padding=3, fontsize=8, color=color_dark_green)
        else:
            ax4.text(0.5, 0.5, "Sin sucursales registradas", ha="center", va="center", color=COLOR_TEXT_MUTED, fontsize=9)

        ax4.set_title("Rendimiento por Sucursal ($)", fontsize=10, fontweight="bold", color=color_dark_green, pad=8)
        ax4.grid(axis="y", linestyle="--", alpha=0.3, color=color_border)
        ax4.tick_params(axis="y", labelsize=8)

        # Montar en Tkinter Canvas
        self.chart_canvas = FigureCanvasTkAgg(fig, master=self.charts_frame)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True)

    # =========================================================================
    # TAB 2: SEMÁFORO DE CADUCIDAD FEFO
    # =========================================================================
    def _build_tab_semaforo(self):
        frame = self.tab_semaforo

        hdr = tk.Frame(frame, bg=COLOR_BG, pady=8)
        hdr.pack(fill="x")

        tk.Label(hdr, text="Filtrar por Sucursal:", font=FONT_BOLD, bg=COLOR_BG, fg=COLOR_TEXT).pack(side="left", padx=(0, 6))
        self.combo_sem_sucursal = ttk.Combobox(hdr, state="readonly", width=22)
        self.combo_sem_sucursal.pack(side="left", padx=(0, 10))
        self.combo_sem_sucursal.bind("<<ComboboxSelected>>", lambda e: self._load_semaforo_data())

        btn_ref_sem = ttk.Button(hdr, text="🔄 Actualizar", style="Secondary.TButton", command=self._load_semaforo_data)
        btn_ref_sem.pack(side="right", padx=5)

        table_card = tk.Frame(frame, bg=COLOR_PANEL, padx=10, pady=10, relief="solid", borderwidth=1, highlightbackground=COLOR_BORDER, highlightthickness=1)
        table_card.pack(fill="both", expand=True, pady=(0, 10))

        cols = ("lote", "medicamento", "codigo", "sucursal", "vence", "dias", "stock", "estado")
        self.tree_semaforo = ttk.Treeview(table_card, columns=cols, show="headings")

        self.tree_semaforo.heading("lote", text="N° Lote")
        self.tree_semaforo.heading("medicamento", text="Medicamento")
        self.tree_semaforo.heading("codigo", text="Cód. Barras")
        self.tree_semaforo.heading("sucursal", text="Sucursal")
        self.tree_semaforo.heading("vence", text="Fecha Vencimiento")
        self.tree_semaforo.heading("dias", text="Días Restantes")
        self.tree_semaforo.heading("stock", text="Stock Disp.")
        self.tree_semaforo.heading("estado", text="Estado de Lote")

        self.tree_semaforo.column("lote", width=110, anchor="center")
        self.tree_semaforo.column("medicamento", width=220, anchor="w")
        self.tree_semaforo.column("codigo", width=105, anchor="center")
        self.tree_semaforo.column("sucursal", width=140, anchor="w")
        self.tree_semaforo.column("vence", width=110, anchor="center")
        self.tree_semaforo.column("dias", width=95, anchor="center")
        self.tree_semaforo.column("stock", width=90, anchor="center")
        self.tree_semaforo.column("estado", width=140, anchor="center")

        self.tree_semaforo.tag_configure("vencido", background="#FFEBEE", foreground="#C62828")
        self.tree_semaforo.tag_configure("critico", background="#FFF3E0", foreground="#E65100")
        self.tree_semaforo.tag_configure("prevencion", background="#FFFDE7", foreground="#F57F17")
        self.tree_semaforo.tag_configure("seguro", background="#E8F5E9", foreground="#2E7D32")

        sb = ttk.Scrollbar(table_card, orient="vertical", command=self.tree_semaforo.yview)
        self.tree_semaforo.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tree_semaforo.pack(fill="both", expand=True)

    # =========================================================================
    # TAB 3: MEDICAMENTOS Y GESTIÓN DE LOTES (MULTI-SUCURSAL)
    # =========================================================================
    def _build_tab_inventory(self):
        frame = self.tab_inventory

        bar = tk.Frame(frame, bg=COLOR_BG, pady=8)
        bar.pack(fill="x")

        btn_new_prod = ttk.Button(bar, text="➕ Nuevo Medicamento", style="Pink.TButton", command=self._show_new_product_modal)
        btn_new_prod.pack(side="left", padx=5)

        btn_new_lot = ttk.Button(bar, text="🏷️ Ingresar Lote a Sucursal", style="Secondary.TButton", command=self._show_new_lot_modal)
        btn_new_lot.pack(side="left", padx=5)

        # Filtro de sucursal para ver stocks independientes
        tk.Label(bar, text="Ver Stock de:", font=FONT_BOLD, bg=COLOR_BG, fg=COLOR_TEXT).pack(side="left", padx=(15, 5))
        self.combo_inv_sucursal = ttk.Combobox(bar, state="readonly", width=22)
        self.combo_inv_sucursal.pack(side="left", padx=(0, 10))
        self.combo_inv_sucursal.bind("<<ComboboxSelected>>", lambda e: self._load_inventory_data())

        btn_ref_inv = ttk.Button(bar, text="🔄 Refrescar", style="Secondary.TButton", command=self._load_inventory_data)
        btn_ref_inv.pack(side="right", padx=5)

        table_card = tk.Frame(frame, bg=COLOR_PANEL, padx=10, pady=10, relief="solid", borderwidth=1, highlightbackground=COLOR_BORDER, highlightthickness=1)
        table_card.pack(fill="both", expand=True, pady=(0, 10))

        cols = ("id", "codigo", "nombre", "principio", "laboratorio", "precio_v", "precio_c", "receta", "stock", "proximo_lote", "vence")
        self.tree_inventory = ttk.Treeview(table_card, columns=cols, show="headings")

        self.tree_inventory.heading("id", text="ID")
        self.tree_inventory.heading("codigo", text="Cód. Barras")
        self.tree_inventory.heading("nombre", text="Nombre")
        self.tree_inventory.heading("principio", text="Principio Activo")
        self.tree_inventory.heading("laboratorio", text="Laboratorio")
        self.tree_inventory.heading("precio_v", text="P. Venta")
        self.tree_inventory.heading("precio_c", text="P. Costo")
        self.tree_inventory.heading("receta", text="Receta")
        self.tree_inventory.heading("stock", text="Stock Sucurs.")
        self.tree_inventory.heading("proximo_lote", text="Próx. Lote")
        self.tree_inventory.heading("vence", text="Próx. Vencimiento")

        self.tree_inventory.column("id", width=35, anchor="center")
        self.tree_inventory.column("codigo", width=105, anchor="center")
        self.tree_inventory.column("nombre", width=180, anchor="w")
        self.tree_inventory.column("principio", width=130, anchor="w")
        self.tree_inventory.column("laboratorio", width=110, anchor="w")
        self.tree_inventory.column("precio_v", width=70, anchor="e")
        self.tree_inventory.column("precio_c", width=70, anchor="e")
        self.tree_inventory.column("receta", width=65, anchor="center")
        self.tree_inventory.column("stock", width=95, anchor="center")
        self.tree_inventory.column("proximo_lote", width=110, anchor="center")
        self.tree_inventory.column("vence", width=100, anchor="center")

        sb = ttk.Scrollbar(table_card, orient="vertical", command=self.tree_inventory.yview)
        self.tree_inventory.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tree_inventory.pack(fill="both", expand=True)

    # =========================================================================
    # TAB 4: GESTIÓN DE SUCURSALES (ALTA Y ADMINISTRACIÓN)
    # =========================================================================
    def _build_tab_branches(self):
        frame = self.tab_branches

        bar = tk.Frame(frame, bg=COLOR_BG, pady=8)
        bar.pack(fill="x")

        btn_new_branch = ttk.Button(bar, text="➕ Nueva Sucursal", style="Pink.TButton", command=self._show_new_branch_modal)
        btn_new_branch.pack(side="left", padx=5)

        btn_ref_branch = ttk.Button(bar, text="🔄 Refrescar", style="Secondary.TButton", command=self._load_branches_data)
        btn_ref_branch.pack(side="right", padx=5)

        table_card = tk.Frame(frame, bg=COLOR_PANEL, padx=10, pady=10, relief="solid", borderwidth=1, highlightbackground=COLOR_BORDER, highlightthickness=1)
        table_card.pack(fill="both", expand=True, pady=(0, 10))

        cols = ("id", "nombre", "direccion", "telefono", "estado")
        self.tree_branches = ttk.Treeview(table_card, columns=cols, show="headings")

        self.tree_branches.heading("id", text="ID")
        self.tree_branches.heading("nombre", text="Nombre de la Sucursal")
        self.tree_branches.heading("direccion", text="Dirección")
        self.tree_branches.heading("telefono", text="Teléfono")
        self.tree_branches.heading("estado", text="Estado")

        self.tree_branches.column("id", width=40, anchor="center")
        self.tree_branches.column("nombre", width=220, anchor="w")
        self.tree_branches.column("direccion", width=340, anchor="w")
        self.tree_branches.column("telefono", width=140, anchor="center")
        self.tree_branches.column("estado", width=100, anchor="center")

        sb = ttk.Scrollbar(table_card, orient="vertical", command=self.tree_branches.yview)
        self.tree_branches.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tree_branches.pack(fill="both", expand=True)

    # =========================================================================
    # TAB 5: USUARIOS Y ROLES (RBAC)
    # =========================================================================
    def _build_tab_users(self):
        frame = self.tab_users

        bar = tk.Frame(frame, bg=COLOR_BG, pady=8)
        bar.pack(fill="x")

        btn_new_user = ttk.Button(bar, text="👤 Nuevo Usuario", style="Pink.TButton", command=self._show_new_user_modal)
        btn_new_user.pack(side="left", padx=5)

        btn_toggle = ttk.Button(bar, text="⚡ Activar / Desactivar", style="Secondary.TButton", command=self._handle_toggle_user)
        btn_toggle.pack(side="left", padx=5)

        btn_ref_users = ttk.Button(bar, text="🔄 Refrescar", style="Secondary.TButton", command=self._load_users_data)
        btn_ref_users.pack(side="right", padx=5)

        table_card = tk.Frame(frame, bg=COLOR_PANEL, padx=10, pady=10, relief="solid", borderwidth=1, highlightbackground=COLOR_BORDER, highlightthickness=1)
        table_card.pack(fill="both", expand=True, pady=(0, 10))

        cols = ("id", "username", "nombre", "rol", "estado", "creado")
        self.tree_users = ttk.Treeview(table_card, columns=cols, show="headings")

        self.tree_users.heading("id", text="ID")
        self.tree_users.heading("username", text="Usuario")
        self.tree_users.heading("nombre", text="Nombre Completo")
        self.tree_users.heading("rol", text="Rol")
        self.tree_users.heading("estado", text="Estado")
        self.tree_users.heading("creado", text="Fecha Registro")

        self.tree_users.column("id", width=40, anchor="center")
        self.tree_users.column("username", width=120, anchor="w")
        self.tree_users.column("nombre", width=220, anchor="w")
        self.tree_users.column("rol", width=110, anchor="center")
        self.tree_users.column("estado", width=100, anchor="center")
        self.tree_users.column("creado", width=140, anchor="center")

        sb = ttk.Scrollbar(table_card, orient="vertical", command=self.tree_users.yview)
        self.tree_users.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tree_users.pack(fill="both", expand=True)

    # =========================================================================
    # TAB 6: REPORTE DE VENTAS
    # =========================================================================
    def _build_tab_sales(self):
        frame = self.tab_sales

        bar = tk.Frame(frame, bg=COLOR_BG, pady=8)
        bar.pack(fill="x")

        btn_detail = ttk.Button(bar, text="🔍 Ver Detalle y Lote Asignado", style="Pink.TButton", command=self._handle_view_sale_detail)
        btn_detail.pack(side="left", padx=5)

        tk.Label(bar, text="Filtrar Sucursal:", font=FONT_BOLD, bg=COLOR_BG, fg=COLOR_TEXT).pack(side="left", padx=(15, 5))
        self.combo_sales_sucursal = ttk.Combobox(bar, state="readonly", width=22)
        self.combo_sales_sucursal.pack(side="left", padx=(0, 10))
        self.combo_sales_sucursal.bind("<<ComboboxSelected>>", lambda e: self._load_sales_data())

        btn_ref_sales = ttk.Button(bar, text="🔄 Refrescar", style="Secondary.TButton", command=self._load_sales_data)
        btn_ref_sales.pack(side="right", padx=5)

        table_card = tk.Frame(frame, bg=COLOR_PANEL, padx=10, pady=10, relief="solid", borderwidth=1, highlightbackground=COLOR_BORDER, highlightthickness=1)
        table_card.pack(fill="both", expand=True, pady=(0, 10))

        cols = ("id", "folio", "sucursal", "fecha", "cajero", "cliente", "total", "metodo", "articulos")
        self.tree_sales = ttk.Treeview(table_card, columns=cols, show="headings")

        self.tree_sales.heading("id", text="ID")
        self.tree_sales.heading("folio", text="Folio")
        self.tree_sales.heading("sucursal", text="Sucursal")
        self.tree_sales.heading("fecha", text="Fecha / Hora")
        self.tree_sales.heading("cajero", text="Cajero")
        self.tree_sales.heading("cliente", text="Cliente")
        self.tree_sales.heading("total", text="Total")
        self.tree_sales.heading("metodo", text="Método Pago")
        self.tree_sales.heading("articulos", text="Cant. Ítems")

        self.tree_sales.column("id", width=35, anchor="center")
        self.tree_sales.column("folio", width=155, anchor="center")
        self.tree_sales.column("sucursal", width=140, anchor="w")
        self.tree_sales.column("fecha", width=130, anchor="center")
        self.tree_sales.column("cajero", width=150, anchor="w")
        self.tree_sales.column("cliente", width=130, anchor="w")
        self.tree_sales.column("total", width=85, anchor="e")
        self.tree_sales.column("metodo", width=110, anchor="center")
        self.tree_sales.column("articulos", width=75, anchor="center")

        sb = ttk.Scrollbar(table_card, orient="vertical", command=self.tree_sales.yview)
        self.tree_sales.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tree_sales.pack(fill="both", expand=True)

        self.tree_sales.bind("<Double-1>", lambda e: self._handle_view_sale_detail())

    # =========================================================================
    # CARGA Y ACTUALIZACIÓN DE DATOS
    # =========================================================================
    def _populate_branch_combos(self):
        sucursales = list_branches(only_active=True)
        self.branch_filter_map = {"Todas las Sucursales": None}
        for s in sucursales:
            self.branch_filter_map[s["nombre"]] = s["id"]

        branch_options = list(self.branch_filter_map.keys())

        for cb in [self.combo_filter_sucursal, self.combo_sem_sucursal, self.combo_inv_sucursal, self.combo_sales_sucursal]:
            cur = cb.get()
            cb.configure(values=branch_options)
            if cur in branch_options:
                cb.set(cur)
            else:
                cb.set("Todas las Sucursales")

    def _on_tab_changed(self):
        idx = self.notebook.index(self.notebook.select())
        if idx == 0:
            self._load_analytics_tab()
        elif idx == 1:
            self._load_semaforo_data()
        elif idx == 2:
            self._load_inventory_data()
        elif idx == 3:
            self._load_branches_data()
        elif idx == 4:
            self._load_users_data()
        elif idx == 5:
            self._load_sales_data()

    def _refresh_all_data(self):
        self._populate_branch_combos()
        self._load_analytics_tab()
        self._load_semaforo_data()
        self._load_inventory_data()
        self._load_branches_data()
        self._load_users_data()
        self._load_sales_data()

    def _load_analytics_tab(self):
        self._populate_branch_combos()
        suc_label = self.combo_filter_sucursal.get()
        suc_id = self.branch_filter_map.get(suc_label)

        periodo_label = self.combo_filter_periodo.get()
        periodo_map = {
            "Este Mes": "mes",
            "Hoy": "hoy",
            "Últimos 7 Días": "7d",
            "Últimos 30 Días": "30d",
            "Historial Completo": "todos"
        }
        date_preset = periodo_map.get(periodo_label, "mes")

        # 1. Calcular KPIs
        kpis = get_kpis_and_metrics(sucursal_id=suc_id, date_preset=date_preset)
        self.kpi_ventas_dia.configure(text=f"${kpis['ventas_hoy']:.2f}")
        self.kpi_ventas_mes.configure(text=f"${kpis['ventas_mes']:.2f}")
        self.kpi_ticket_prom.configure(text=f"${kpis['ticket_promedio']:.2f}")
        self.kpi_ingresos_filtro.configure(text=f"${kpis['total_ingresos']:.2f}")
        self.kpi_transacciones.configure(text=f"{kpis['total_transacciones']} ventas ({kpis['total_articulos']} u.)")

        # 2. Renderizar los 4 gráficos interactivos de Matplotlib
        self._render_matplotlib_charts(sucursal_id=suc_id, date_preset=date_preset)

    def _load_semaforo_data(self):
        suc_label = self.combo_sem_sucursal.get()
        suc_id = self.branch_filter_map.get(suc_label)

        self.tree_semaforo.delete(*self.tree_semaforo.get_children())
        report = check_batch_expirations(days_threshold=60, sucursal_id=suc_id)

        for item in report["vencidos"]:
            self.tree_semaforo.insert("", "end", values=(
                item["numero_lote"], item["producto"], item["codigo"], item["sucursal"],
                item["fecha_vencimiento"], f"VENCIDO hace {abs(item['dias_restantes'])}d", item["stock"], "🔴 VENCIDO"
            ), tags=("vencido",))

        for item in report["criticos"]:
            self.tree_semaforo.insert("", "end", values=(
                item["numero_lote"], item["producto"], item["codigo"], item["sucursal"],
                item["fecha_vencimiento"], f"{item['dias_restantes']} días", item["stock"], "🟠 CRÍTICO"
            ), tags=("critico",))

        for item in report["por_vencer"]:
            self.tree_semaforo.insert("", "end", values=(
                item["numero_lote"], item["producto"], item["codigo"], item["sucursal"],
                item["fecha_vencimiento"], f"{item['dias_restantes']} días", item["stock"], "🟡 PREVENCIÓN"
            ), tags=("prevencion",))

        for item in report["seguros"][:15]:
            self.tree_semaforo.insert("", "end", values=(
                item["numero_lote"], item["producto"], item["codigo"], item["sucursal"],
                item["fecha_vencimiento"], f"{item['dias_restantes']} días", item["stock"], "🟢 ÓPTIMO"
            ), tags=("seguro",))

    def _load_inventory_data(self):
        suc_label = self.combo_inv_sucursal.get()
        suc_id = self.branch_filter_map.get(suc_label)

        self.tree_inventory.delete(*self.tree_inventory.get_children())
        prods = get_all_products_with_stock(sucursal_id=suc_id)

        for p in prods:
            self.tree_inventory.insert("", "end", values=(
                p["id"], p["codigo_barras"], p["nombre"], p["principio_activo"] or "N/A",
                p["laboratorio"] or "N/A", f"${p['precio_venta']:.2f}", f"${p['precio_costo']:.2f}",
                "Sí" if p["requiere_receta"] else "No", p["stock_total"], p["proximo_lote_numero"], p["proximo_lote_vence"]
            ))

    def _load_branches_data(self):
        self.tree_branches.delete(*self.tree_branches.get_children())
        sucursales = list_branches(only_active=False)
        for s in sucursales:
            estado = "✅ Activa" if s["activo"] else "❌ Inactiva"
            self.tree_branches.insert("", "end", values=(
                s["id"], s["nombre"], s["direccion"], s["telefono"], estado
            ))

    def _load_users_data(self):
        self.tree_users.delete(*self.tree_users.get_children())
        users = list_users()
        for u in users:
            estado = "✅ Activo" if u["activo"] else "❌ Inactivo"
            self.tree_users.insert("", "end", values=(
                u["id"], u["username"], u["nombre_completo"], u["rol"].upper(), estado, u["created_at"]
            ))

    def _load_sales_data(self):
        suc_label = self.combo_sales_sucursal.get()
        suc_id = self.branch_filter_map.get(suc_label)

        self.tree_sales.delete(*self.tree_sales.get_children())
        sales = get_sales_history(limit=50, sucursal_id=suc_id)
        for s in sales:
            self.tree_sales.insert("", "end", values=(
                s["id"], s["folio"], s.get("sucursal", "N/A"), s["fecha"], s["cajero"], s["cliente"],
                f"${s['total']:.2f}", s["metodo_pago"], s["total_articulos"]
            ))

    # =========================================================================
    # MODALES: ALTA DE SUCURSAL, MEDICAMENTO, LOTE Y USUARIO
    # =========================================================================
    def _show_new_branch_modal(self):
        modal = tk.Toplevel(self)
        modal.title("Registrar Nueva Sucursal")
        modal.geometry("420x360")
        modal.configure(bg=COLOR_BG)
        modal.transient(self)
        modal.grab_set()

        hdr = tk.Frame(modal, bg=COLOR_PRIMARY, padx=15, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🏢 Nueva Sucursal de Farmacia", font=FONT_TITLE, bg=COLOR_PRIMARY, fg=COLOR_TEXT_WHITE).pack(anchor="w")

        f = tk.Frame(modal, bg=COLOR_BG, padx=20, pady=15)
        f.pack(fill="both", expand=True)

        tk.Label(f, text="Nombre de la Sucursal (*):", font=FONT_BOLD, bg=COLOR_BG, fg=COLOR_TEXT).grid(row=0, column=0, sticky="w", pady=6)
        ent_nom = ttk.Entry(f, font=FONT_REGULAR)
        ent_nom.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=6)

        tk.Label(f, text="Dirección Completa:", font=FONT_BOLD, bg=COLOR_BG, fg=COLOR_TEXT).grid(row=1, column=0, sticky="w", pady=6)
        ent_dir = ttk.Entry(f, font=FONT_REGULAR)
        ent_dir.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=6)

        tk.Label(f, text="Teléfono de Contacto:", font=FONT_BOLD, bg=COLOR_BG, fg=COLOR_TEXT).grid(row=2, column=0, sticky="w", pady=6)
        ent_tel = ttk.Entry(f, font=FONT_REGULAR)
        ent_tel.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=6)

        f.columnconfigure(1, weight=1)

        def save_branch():
            nom = ent_nom.get().strip()
            dire = ent_dir.get().strip()
            tel = ent_tel.get().strip()

            ok, msg, suc_id = create_branch(nom, dire, tel)
            if ok:
                messagebox.showinfo("Éxito", msg, parent=modal)
                modal.destroy()
                self._load_branches_data()
                self._populate_branch_combos()
            else:
                messagebox.showerror("Error", msg, parent=modal)

        btn_save = ttk.Button(modal, text="Guardar Sucursal", style="Pink.TButton", command=save_branch)
        btn_save.pack(fill="x", padx=20, pady=(0, 15), ipady=4)

    def _show_new_product_modal(self):
        modal = tk.Toplevel(self)
        modal.title("Nuevo Medicamento")
        modal.geometry("450x520")
        modal.configure(bg=COLOR_BG)
        modal.transient(self)
        modal.grab_set()

        hdr = tk.Frame(modal, bg=COLOR_PRIMARY, padx=15, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="💊 Registrar Medicamento", font=FONT_TITLE, bg=COLOR_PRIMARY, fg=COLOR_TEXT_WHITE).pack(anchor="w")

        f = tk.Frame(modal, bg=COLOR_BG, padx=20, pady=15)
        f.pack(fill="both", expand=True)

        fields = [
            ("Código de Barras (*):", "entry_cod"),
            ("Nombre Comercial (*):", "entry_nom"),
            ("Principio Activo:", "entry_pa"),
            ("Laboratorio:", "entry_lab"),
            ("Precio Venta ($) (*):", "entry_pv"),
            ("Precio Costo ($):", "entry_pc"),
        ]
        entries = {}

        for i, (label_txt, var_name) in enumerate(fields):
            tk.Label(f, text=label_txt, font=FONT_BOLD, bg=COLOR_BG, fg=COLOR_TEXT).grid(row=i, column=0, sticky="w", pady=4)
            ent = ttk.Entry(f, font=FONT_REGULAR, width=28)
            ent.grid(row=i, column=1, sticky="ew", padx=(8, 0), pady=4)
            entries[var_name] = ent

        f.columnconfigure(1, weight=1)

        var_receta = tk.BooleanVar(value=False)
        chk = tk.Checkbutton(f, text="Requiere Receta Médica Controlada", variable=var_receta, bg=COLOR_BG, fg=COLOR_TEXT, font=FONT_REGULAR)
        chk.grid(row=len(fields), column=1, sticky="w", pady=8)

        def save():
            cod = entries["entry_cod"].get().strip()
            nom = entries["entry_nom"].get().strip()
            pa = entries["entry_pa"].get().strip()
            lab = entries["entry_lab"].get().strip()
            try:
                pv = float(entries["entry_pv"].get().strip())
                pc = float(entries["entry_pc"].get().strip() or "0")
            except ValueError:
                messagebox.showerror("Error", "Los precios deben ser numéricos.", parent=modal)
                return

            ok, msg, prod_id = create_product(
                codigo_barras=cod, nombre=nom, principio_activo=pa, laboratorio=lab,
                precio_venta=pv, precio_costo=pc, requiere_receta=var_receta.get()
            )
            if ok:
                messagebox.showinfo("Éxito", msg, parent=modal)
                modal.destroy()
                self._load_inventory_data()
            else:
                messagebox.showerror("Error", msg, parent=modal)

        btn_save = ttk.Button(modal, text="Guardar Medicamento", style="Pink.TButton", command=save)
        btn_save.pack(fill="x", padx=20, pady=(0, 15), ipady=4)

    def _show_new_lot_modal(self):
        modal = tk.Toplevel(self)
        modal.title("Ingresar Lote con Vencimiento a Sucursal")
        modal.geometry("480x470")
        modal.configure(bg=COLOR_BG)
        modal.transient(self)
        modal.grab_set()

        hdr = tk.Frame(modal, bg=COLOR_PRIMARY, padx=15, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🏷️ Ingreso de Lote a Sucursal", font=FONT_TITLE, bg=COLOR_PRIMARY, fg=COLOR_TEXT_WHITE).pack(anchor="w")

        f = tk.Frame(modal, bg=COLOR_BG, padx=20, pady=15)
        f.pack(fill="both", expand=True)

        # Sucursal destino
        sucursales = list_branches(only_active=True)
        branch_map = {s["nombre"]: s["id"] for s in sucursales}

        tk.Label(f, text="Sucursal Destino (*):", font=FONT_BOLD, bg=COLOR_BG, fg=COLOR_PRIMARY_ACTIVE).grid(row=0, column=0, sticky="w", pady=6)
        combo_suc = ttk.Combobox(f, values=list(branch_map.keys()), state="readonly", width=28)
        if branch_map:
            combo_suc.current(0)
        combo_suc.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=6)

        prods = get_all_products_with_stock()
        prod_map = {f"{p['nombre']} [{p['codigo_barras']}]": p["id"] for p in prods}

        tk.Label(f, text="Medicamento (*):", font=FONT_BOLD, bg=COLOR_BG, fg=COLOR_TEXT).grid(row=1, column=0, sticky="w", pady=6)
        combo_prods = ttk.Combobox(f, values=list(prod_map.keys()), state="readonly", width=28)
        if prod_map:
            combo_prods.current(0)
        combo_prods.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=6)

        tk.Label(f, text="Número de Lote (*):", font=FONT_BOLD, bg=COLOR_BG, fg=COLOR_TEXT).grid(row=2, column=0, sticky="w", pady=6)
        ent_lote = ttk.Entry(f, font=FONT_REGULAR)
        ent_lote.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=6)

        tk.Label(f, text="Fecha Vencimiento (*):", font=FONT_BOLD, bg=COLOR_BG, fg=COLOR_TEXT).grid(row=3, column=0, sticky="w", pady=6)
        ent_vence = ttk.Entry(f, font=FONT_REGULAR)
        ent_vence.insert(0, "YYYY-MM-DD")
        ent_vence.grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=6)

        tk.Label(f, text="Stock Inicial (Unidades):", font=FONT_BOLD, bg=COLOR_BG, fg=COLOR_TEXT).grid(row=4, column=0, sticky="w", pady=6)
        ent_stock = ttk.Entry(f, font=FONT_REGULAR)
        ent_stock.insert(0, "40")
        ent_stock.grid(row=4, column=1, sticky="ew", padx=(8, 0), pady=6)

        tk.Label(f, text="Costo de Compra ($):", font=FONT_BOLD, bg=COLOR_BG, fg=COLOR_TEXT).grid(row=5, column=0, sticky="w", pady=6)
        ent_costo = ttk.Entry(f, font=FONT_REGULAR)
        ent_costo.insert(0, "0.00")
        ent_costo.grid(row=5, column=1, sticky="ew", padx=(8, 0), pady=6)

        f.columnconfigure(1, weight=1)

        def save_lot():
            suc_name = combo_suc.get()
            prod_text = combo_prods.get()
            if not suc_name or not prod_text:
                messagebox.showerror("Error", "Seleccione sucursal y medicamento.", parent=modal)
                return

            suc_id = branch_map[suc_name]
            prod_id = prod_map[prod_text]
            lot_num = ent_lote.get().strip()
            vence_str = ent_vence.get().strip()

            try:
                stock_val = int(ent_stock.get().strip())
                cost_val = float(ent_costo.get().strip() or "0")
            except ValueError:
                messagebox.showerror("Error", "Stock debe ser entero y costo numérico.", parent=modal)
                return

            ok, msg = create_batch(prod_id, lot_num, vence_str, stock_val, cost_val, id_sucursal=suc_id)
            if ok:
                messagebox.showinfo("Éxito", msg, parent=modal)
                modal.destroy()
                self._load_inventory_data()
                self._load_semaforo_data()
            else:
                messagebox.showerror("Error", msg, parent=modal)

        btn_save = ttk.Button(modal, text="Guardar Lote en Sucursal", style="Pink.TButton", command=save_lot)
        btn_save.pack(fill="x", padx=20, pady=(0, 15), ipady=4)

    def _show_new_user_modal(self):
        modal = tk.Toplevel(self)
        modal.title("Nuevo Usuario del Sistema")
        modal.geometry("420x400")
        modal.configure(bg=COLOR_BG)
        modal.transient(self)
        modal.grab_set()

        hdr = tk.Frame(modal, bg=COLOR_PRIMARY, padx=15, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="👤 Crear Usuario", font=FONT_TITLE, bg=COLOR_PRIMARY, fg=COLOR_TEXT_WHITE).pack(anchor="w")

        f = tk.Frame(modal, bg=COLOR_BG, padx=20, pady=15)
        f.pack(fill="both", expand=True)

        tk.Label(f, text="Nombre de Usuario (*):", font=FONT_BOLD, bg=COLOR_BG, fg=COLOR_TEXT).grid(row=0, column=0, sticky="w", pady=6)
        ent_user = ttk.Entry(f, font=FONT_REGULAR)
        ent_user.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=6)

        tk.Label(f, text="Nombre Completo (*):", font=FONT_BOLD, bg=COLOR_BG, fg=COLOR_TEXT).grid(row=1, column=0, sticky="w", pady=6)
        ent_name = ttk.Entry(f, font=FONT_REGULAR)
        ent_name.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=6)

        tk.Label(f, text="Contraseña (*):", font=FONT_BOLD, bg=COLOR_BG, fg=COLOR_TEXT).grid(row=2, column=0, sticky="w", pady=6)
        ent_pass = ttk.Entry(f, font=FONT_REGULAR, show="•")
        ent_pass.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=6)

        tk.Label(f, text="Rol del Sistema (*):", font=FONT_BOLD, bg=COLOR_BG, fg=COLOR_TEXT).grid(row=3, column=0, sticky="w", pady=6)
        roles = list_roles()
        combo_rol = ttk.Combobox(f, values=roles, state="readonly")
        if roles:
            combo_rol.set("empleado" if "empleado" in roles else roles[0])
        combo_rol.grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=6)

        f.columnconfigure(1, weight=1)

        def save_user():
            u = ent_user.get().strip()
            nom = ent_name.get().strip()
            p = ent_pass.get()
            rol = combo_rol.get()

            ok, msg = create_user(u, p, nom, rol)
            if ok:
                messagebox.showinfo("Éxito", msg, parent=modal)
                modal.destroy()
                self._load_users_data()
            else:
                messagebox.showerror("Error", msg, parent=modal)

        btn_save = ttk.Button(modal, text="Registrar Usuario", style="Pink.TButton", command=save_user)
        btn_save.pack(fill="x", padx=20, pady=(0, 15), ipady=4)

    def _handle_toggle_user(self):
        sel = self.tree_users.selection()
        if not sel:
            messagebox.showinfo("Seleccionar", "Seleccione un usuario de la tabla.", parent=self)
            return

        values = self.tree_users.item(sel[0], "values")
        user_id = int(values[0])
        ok, msg = toggle_user_status(user_id)
        if ok:
            messagebox.showinfo("Estado", msg, parent=self)
            self._load_users_data()
        else:
            messagebox.showwarning("Atención", msg, parent=self)

    def _handle_view_sale_detail(self):
        sel = self.tree_sales.selection()
        if not sel:
            messagebox.showinfo("Seleccionar", "Seleccione una venta para auditar sus lotes.", parent=self)
            return

        values = self.tree_sales.item(sel[0], "values")
        sale_id = int(values[0])
        sale_data = get_sale_details(sale_id)
        if not sale_data:
            messagebox.showerror("Error", "No se encontraron detalles de la venta.", parent=self)
            return

        show_ticket_modal(self.winfo_toplevel(), sale_data)
