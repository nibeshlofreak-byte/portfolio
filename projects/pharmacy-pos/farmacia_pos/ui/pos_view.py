"""
Pantalla de Ventas / Punto de Venta (POS) - FarmaShield
Pilar 2 (RBAC Empleado/Caja), Paleta FarmaShield Verde/Blanco Hueso/Blanco Puro y Deducción FEFO.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from decimal import Decimal
from typing import Callable, Optional
from PIL import Image, ImageTk

from .styles import (
    COLOR_BG, COLOR_PANEL, COLOR_PRIMARY, COLOR_PRIMARY_HOVER,
    COLOR_PRIMARY_ACTIVE, COLOR_PRIMARY_LIGHT, COLOR_BORDER, COLOR_TEXT,
    COLOR_TEXT_MUTED, COLOR_TEXT_WHITE, COLOR_SUCCESS, COLOR_WARNING,
    COLOR_DANGER, FONT_TITLE, FONT_TITLE_LARGE, FONT_SUBTITLE, FONT_BOLD,
    FONT_REGULAR, FONT_SMALL, FONT_MONO_BOLD
)
from ..services.inventory_service import search_products, get_product_by_barcode, list_branches
from ..services.sales_service import ShoppingCart, process_sale
from ..services.auth_service import is_admin, get_current_user, get_current_branch, get_current_branch_id, set_current_branch
from ..utils.printer import show_ticket_modal


class POSView(tk.Frame):
    """
    Vista de ventas para el personal de caja y farmacéuticos en FarmaShield.
    Integra el carrito de compras con validación y descuento en tiempo real
    del lote más próximo a vencer (Algoritmo FEFO) específico de la sucursal seleccionada.
    """

    def __init__(self, parent: tk.Tk or tk.Frame, on_logout: Callable, on_open_admin: Optional[Callable] = None):
        super().__init__(parent, bg=COLOR_BG)
        self.parent = parent
        self.on_logout = on_logout
        self.on_open_admin = on_open_admin

        self.sucursal = get_current_branch()
        self.sucursal_id = get_current_branch_id()

        self.cart = ShoppingCart(tasa_iva=0.16, sucursal_id=self.sucursal_id)
        self.last_sale_ticket = None
        self.logo_img = None

        self._load_logo()
        self._build_ui()
        self._load_catalog()

    def _load_logo(self):
        """Carga el logo oficial FarmaShield para la barra de ventas."""
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            logo_path = os.path.join(base_dir, "assets", "logo_header.png")
            if os.path.exists(logo_path):
                pil_img = Image.open(logo_path)
                self.logo_img = ImageTk.PhotoImage(pil_img)
        except Exception as e:
            print(f"[POS] No se pudo cargar logo: {e}")
            self.logo_img = None

    def _build_ui(self):
        # 1. BARRA SUPERIOR (HEADER VERDE FARMASHIELD)
        header = tk.Frame(self, bg=COLOR_PRIMARY, padx=20, pady=10)
        header.pack(fill="x")

        # Título y farmacia
        left_header = tk.Frame(header, bg=COLOR_PRIMARY)
        left_header.pack(side="left")

        if self.logo_img:
            lbl_img = tk.Label(left_header, image=self.logo_img, bg=COLOR_PRIMARY)
            lbl_img.pack(side="left", padx=(0, 10))

        text_box_h = tk.Frame(left_header, bg=COLOR_PRIMARY)
        text_box_h.pack(side="left")

        lbl_logo = tk.Label(
            text_box_h,
            text="FarmaShield",
            font=FONT_TITLE,
            bg=COLOR_PRIMARY,
            fg=COLOR_TEXT_WHITE
        )
        lbl_logo.pack(anchor="w")

        lbl_slogan = tk.Label(
            text_box_h,
            text="Terminal de Ventas y Despacho",
            font=FONT_SMALL,
            bg=COLOR_PRIMARY,
            fg=COLOR_BG
        )
        lbl_slogan.pack(anchor="w")

        # Información del usuario en sesión y acciones
        right_header = tk.Frame(header, bg=COLOR_PRIMARY)
        right_header.pack(side="right")

        user = get_current_user()
        cajero_info = f"👤 {user.nombre_completo if user else 'Cajero'} ({user.rol.nombre.upper() if user and user.rol else 'CAJA'})"

        lbl_user = tk.Label(
            right_header,
            text=cajero_info,
            font=FONT_BOLD,
            bg=COLOR_PRIMARY,
            fg=COLOR_TEXT_WHITE
        )
        lbl_user.pack(side="left", padx=(0, 10))

        # Indicador de Sucursal de Trabajo
        suc_nombre = self.sucursal.nombre if self.sucursal else "Farmacia Central"
        self.lbl_branch_badge = tk.Label(
            right_header,
            text=f"🏪 {suc_nombre}",
            font=FONT_BOLD,
            bg=COLOR_PRIMARY_ACTIVE,
            fg=COLOR_TEXT_WHITE,
            padx=10,
            pady=3,
            relief="solid",
            borderwidth=1
        )
        self.lbl_branch_badge.pack(side="left", padx=(0, 10))

        btn_switch_branch = ttk.Button(
            right_header,
            text="Cambiar Sucursal",
            style="Secondary.TButton",
            command=self._show_change_branch_modal
        )
        btn_switch_branch.pack(side="left", padx=(0, 10))

        # Botón para volver a Admin si el usuario tiene rol 'admin'
        if is_admin() and self.on_open_admin:
            btn_admin = ttk.Button(
                right_header,
                text="📊 Panel Administrador",
                style="Secondary.TButton",
                command=self.on_open_admin
            )
            btn_admin.pack(side="left", padx=5)

        btn_logout = ttk.Button(
            right_header,
            text="🚪 Cerrar Sesión",
            style="Secondary.TButton",
            command=self.on_logout
        )
        btn_logout.pack(side="left", padx=5)

        # 2. CUERPO PRINCIPAL (2 COLUMNAS: CATÁLOGO/BÚSQUEDA Y CARRITO/COBRO)
        body = tk.Frame(self, bg=COLOR_BG, padx=15, pady=12)
        body.pack(fill="both", expand=True)

        # COLUMNA IZQUIERDA: Catálogo y Búsqueda de Medicamentos (55% ancho)
        col_left = tk.Frame(body, bg=COLOR_BG)
        col_left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Barra de búsqueda con tonos rosas
        search_card = tk.Frame(
            col_left,
            bg=COLOR_PANEL,
            padx=12,
            pady=10,
            relief="solid",
            borderwidth=1,
            highlightbackground=COLOR_BORDER,
            highlightthickness=1
        )
        search_card.pack(fill="x", pady=(0, 10))

        lbl_search = tk.Label(
            search_card,
            text="🔍 Buscar Medicamento por Nombre o Código de Barras:",
            font=FONT_BOLD,
            bg=COLOR_PANEL,
            fg=COLOR_PRIMARY_ACTIVE
        )
        lbl_search.pack(anchor="w", pady=(0, 5))

        search_bar = tk.Frame(search_card, bg=COLOR_PANEL)
        search_bar.pack(fill="x")

        self.entry_search = ttk.Entry(search_bar, font=FONT_REGULAR)
        self.entry_search.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 8))
        self.entry_search.focus_set()

        lbl_q = tk.Label(search_bar, text="Cantidad:", font=FONT_BOLD, bg=COLOR_PANEL, fg=COLOR_TEXT)
        lbl_q.pack(side="left", padx=(0, 4))

        self.entry_qty = ttk.Entry(search_bar, font=FONT_BOLD, width=5, justify="center")
        self.entry_qty.insert(0, "1")
        self.entry_qty.pack(side="left", ipady=4, padx=(0, 6))

        btn_add_quick = ttk.Button(
            search_bar,
            text="➕ Agregar al Carrito",
            style="Pink.TButton",
            command=self._add_selected_to_cart
        )
        btn_add_quick.pack(side="left", padx=2)

        btn_search = ttk.Button(
            search_bar,
            text="Buscar",
            style="Secondary.TButton",
            command=self._handle_search
        )
        btn_search.pack(side="left", padx=2)

        btn_clear_search = ttk.Button(
            search_bar,
            text="Ver Todos",
            style="Secondary.TButton",
            command=self._load_catalog
        )
        btn_clear_search.pack(side="left", padx=2)

        # Tecla Enter
        self.entry_search.bind("<Return>", lambda e: self._on_search_enter())
        self.entry_qty.bind("<Return>", lambda e: self._add_selected_to_cart())

        # Tabla de Medicamentos
        table_frame = tk.Frame(
            col_left,
            bg=COLOR_PANEL,
            relief="solid",
            borderwidth=1,
            highlightbackground=COLOR_BORDER,
            highlightthickness=1
        )
        table_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Título de sección limpio en blanco puro
        table_title_bar = tk.Frame(table_frame, bg=COLOR_PANEL, padx=10, pady=6)
        table_title_bar.pack(fill="x")
        lbl_tbl_title = tk.Label(
            table_title_bar,
            text="📦 Catálogo de Medicamentos Disponibles",
            font=FONT_BOLD,
            bg=COLOR_PANEL,
            fg=COLOR_PRIMARY_ACTIVE
        )
        lbl_tbl_title.pack(side="left")

        lbl_hint = tk.Label(
            table_title_bar,
            text="* Doble clic para agregar la cantidad indicada",
            font=FONT_SMALL,
            bg=COLOR_PANEL,
            fg=COLOR_TEXT_MUTED
        )
        lbl_hint.pack(side="right")

        # Treeview de productos
        columns = ("id", "codigo", "nombre", "precio", "stock", "lote_fefo", "vence", "alerta")
        self.tree_prods = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        self.tree_prods.heading("id", text="ID")
        self.tree_prods.heading("codigo", text="Cód. Barras")
        self.tree_prods.heading("nombre", text="Medicamento / Presentación")
        self.tree_prods.heading("precio", text="Precio")
        self.tree_prods.heading("stock", text="Stock Disp.")
        self.tree_prods.heading("lote_fefo", text="Lote Asignado")
        self.tree_prods.heading("vence", text="Vencimiento")
        self.tree_prods.heading("alerta", text="Estado")

        self.tree_prods.column("id", width=35, anchor="center")
        self.tree_prods.column("codigo", width=105, anchor="center")
        self.tree_prods.column("nombre", width=220, anchor="w")
        self.tree_prods.column("precio", width=70, anchor="e")
        self.tree_prods.column("stock", width=75, anchor="center")
        self.tree_prods.column("lote_fefo", width=110, anchor="center")
        self.tree_prods.column("vence", width=90, anchor="center")
        self.tree_prods.column("alerta", width=140, anchor="w")

        # Tags para colores semánticos
        self.tree_prods.tag_configure("warn", background="#FFF3E0", foreground="#E65100")
        self.tree_prods.tag_configure("danger", background="#FFEBEE", foreground="#D32F2F")
        self.tree_prods.tag_configure("ok", background="#FFFFFF")

        scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree_prods.yview)
        self.tree_prods.configure(yscrollcommand=scrollbar_y.set)

        scrollbar_y.pack(side="right", fill="y")
        self.tree_prods.pack(side="left", fill="both", expand=True)

        self.tree_prods.bind("<Double-1>", lambda e: self._add_selected_to_cart())

        # COLUMNA DERECHA: Carrito de Compras y Cobro (45% ancho)
        col_right = tk.Frame(body, bg=COLOR_BG)
        col_right.pack(side="right", fill="both", expand=True)

        cart_panel = tk.Frame(
            col_right,
            bg=COLOR_PANEL,
            padx=14,
            pady=12,
            relief="solid",
            borderwidth=1,
            highlightbackground=COLOR_BORDER,
            highlightthickness=1
        )
        cart_panel.pack(fill="both", expand=True)

        # Encabezado Carrito
        cart_hdr = tk.Frame(cart_panel, bg=COLOR_PANEL)
        cart_hdr.pack(fill="x", pady=(0, 8))

        lbl_cart_title = tk.Label(
            cart_hdr,
            text="🛒 Carrito de Venta",
            font=FONT_TITLE,
            bg=COLOR_PANEL,
            fg=COLOR_PRIMARY_ACTIVE
        )
        lbl_cart_title.pack(side="left")

        btn_clear_cart = ttk.Button(
            cart_hdr,
            text="🗑️ Vaciar Carrito",
            style="Secondary.TButton",
            command=self._clear_cart
        )
        btn_clear_cart.pack(side="right")

        # Tabla del Carrito
        cart_table_frame = tk.Frame(cart_panel, bg=COLOR_PANEL)
        cart_table_frame.pack(fill="both", expand=True, pady=(0, 10))

        cart_cols = ("nombre", "lote", "cant", "precio", "subtotal")
        self.tree_cart = ttk.Treeview(
            cart_table_frame,
            columns=cart_cols,
            show="headings",
            height=6
        )

        self.tree_cart.heading("nombre", text="Medicamento")
        self.tree_cart.heading("lote", text="Lote")
        self.tree_cart.heading("cant", text="Cant.")
        self.tree_cart.heading("precio", text="P. Unit")
        self.tree_cart.heading("subtotal", text="Total")

        self.tree_cart.column("nombre", width=170, anchor="w")
        self.tree_cart.column("lote", width=95, anchor="center")
        self.tree_cart.column("cant", width=50, anchor="center")
        self.tree_cart.column("precio", width=65, anchor="e")
        self.tree_cart.column("subtotal", width=75, anchor="e")

        cart_scroll = ttk.Scrollbar(cart_table_frame, orient="vertical", command=self.tree_cart.yview)
        self.tree_cart.configure(yscrollcommand=cart_scroll.set)

        cart_scroll.pack(side="right", fill="y")
        self.tree_cart.pack(side="left", fill="both", expand=True)
        self.tree_cart.bind("<Double-1>", lambda e: self._set_cart_item_quantity())

        # Botones de ajuste de cantidad en carrito
        cart_btns = tk.Frame(cart_panel, bg=COLOR_PANEL)
        cart_btns.pack(fill="x", pady=(0, 10))

        btn_qty_edit = ttk.Button(cart_btns, text="✏️ Cambiar Cantidad", style="Secondary.TButton", command=self._set_cart_item_quantity)
        btn_qty_edit.pack(side="left", padx=2)

        btn_rem = ttk.Button(cart_btns, text="❌ Quitar", style="Danger.TButton", command=self._remove_cart_item)
        btn_rem.pack(side="left", padx=2)

        # Panel de Alertas FEFO en tiempo de venta
        self.lbl_fefo_alert = tk.Label(
            cart_panel,
            text="",
            font=FONT_SMALL,
            bg=COLOR_PANEL,
            fg=COLOR_WARNING,
            wraplength=360
        )
        self.lbl_fefo_alert.pack(fill="x", pady=(0, 6))

        # Panel de Totales y Liquidación (Blanco Puro)
        tot_frame = tk.Frame(
            cart_panel,
            bg=COLOR_PANEL,
            padx=12,
            pady=10,
            relief="solid",
            borderwidth=1,
            highlightbackground=COLOR_BORDER,
            highlightthickness=1
        )
        tot_frame.pack(fill="x", pady=(0, 10))

        # Subtotal e IVA
        sub_row = tk.Frame(tot_frame, bg=COLOR_PANEL)
        sub_row.pack(fill="x")
        tk.Label(sub_row, text="Subtotal:", font=FONT_REGULAR, bg=COLOR_PANEL, fg=COLOR_TEXT).pack(side="left")
        self.lbl_subtotal = tk.Label(sub_row, text="$0.00", font=FONT_BOLD, bg=COLOR_PANEL, fg=COLOR_TEXT)
        self.lbl_subtotal.pack(side="right")

        iva_row = tk.Frame(tot_frame, bg=COLOR_PANEL)
        iva_row.pack(fill="x", pady=2)
        tk.Label(iva_row, text="I.V.A. (16%):", font=FONT_REGULAR, bg=COLOR_PANEL, fg=COLOR_TEXT).pack(side="left")
        self.lbl_iva = tk.Label(iva_row, text="$0.00", font=FONT_BOLD, bg=COLOR_PANEL, fg=COLOR_TEXT)
        self.lbl_iva.pack(side="right")

        # Total Grande en Verde FarmaShield
        tot_row = tk.Frame(tot_frame, bg=COLOR_PANEL)
        tot_row.pack(fill="x", pady=(6, 0))
        tk.Label(tot_row, text="TOTAL A COBRAR:", font=FONT_SUBTITLE, bg=COLOR_PANEL, fg=COLOR_PRIMARY_ACTIVE).pack(side="left")
        self.lbl_total = tk.Label(tot_row, text="$0.00", font=FONT_TITLE_LARGE, bg=COLOR_PANEL, fg=COLOR_PRIMARY_ACTIVE)
        self.lbl_total.pack(side="right")

        # Formulario de Cobro
        pay_frame = tk.Frame(cart_panel, bg=COLOR_PANEL)
        pay_frame.pack(fill="x", pady=(0, 10))

        # Método de Pago
        lbl_met = tk.Label(pay_frame, text="Método de Pago:", font=FONT_BOLD, bg=COLOR_PANEL, fg=COLOR_TEXT)
        lbl_met.grid(row=0, column=0, sticky="w", pady=4)

        self.combo_metodo = ttk.Combobox(
            pay_frame,
            values=["Efectivo", "Tarjeta de Débito", "Tarjeta de Crédito", "Transferencia"],
            state="readonly",
            font=FONT_REGULAR
        )
        self.combo_metodo.set("Efectivo")
        self.combo_metodo.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=4)
        self.combo_metodo.bind("<<ComboboxSelected>>", lambda e: self._on_payment_method_change())

        # Cliente
        lbl_cli = tk.Label(pay_frame, text="Cliente:", font=FONT_BOLD, bg=COLOR_PANEL, fg=COLOR_TEXT)
        lbl_cli.grid(row=1, column=0, sticky="w", pady=4)

        self.entry_cliente = ttk.Entry(pay_frame, font=FONT_REGULAR)
        self.entry_cliente.insert(0, "Público General")
        self.entry_cliente.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=4)

        # Monto Recibido
        self.lbl_recibido = tk.Label(pay_frame, text="Monto Recibido ($):", font=FONT_BOLD, bg=COLOR_PANEL, fg=COLOR_TEXT)
        self.lbl_recibido.grid(row=2, column=0, sticky="w", pady=4)

        self.entry_recibido = ttk.Entry(pay_frame, font=FONT_BOLD)
        self.entry_recibido.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=4)
        self.entry_recibido.bind("<KeyRelease>", lambda e: self._calculate_change())

        # Cambio
        lbl_cam = tk.Label(pay_frame, text="Cambio a Devolver:", font=FONT_BOLD, bg=COLOR_PANEL, fg=COLOR_TEXT)
        lbl_cam.grid(row=3, column=0, sticky="w", pady=4)

        self.lbl_cambio = tk.Label(
            pay_frame,
            text="$0.00",
            font=FONT_TITLE,
            bg=COLOR_PANEL,
            fg=COLOR_SUCCESS
        )
        self.lbl_cambio.grid(row=3, column=1, sticky="w", padx=(8, 0), pady=4)

        pay_frame.columnconfigure(1, weight=1)

        # Botón de Cobro Gigante en Rosa Acento
        self.btn_checkout = ttk.Button(
            cart_panel,
            text="💳 COBRAR E IMPRIMIR TICKET",
            style="Accent.TButton",
            command=self._handle_checkout
        )
        self.btn_checkout.pack(fill="x", ipady=6, pady=(4, 6))

        # Botón Ver Último Ticket
        self.btn_last_ticket = ttk.Button(
            cart_panel,
            text="🧾 Ver Último Ticket",
            style="Secondary.TButton",
            command=self._show_last_ticket
        )
        self.btn_last_ticket.pack(fill="x")

        # Atajos de Teclado
        self.bind_all("<F12>", lambda e: self._handle_checkout())

    def _load_catalog(self, search_text: str = ""):
        """Carga los productos y sus lotes FEFO disponibles en la sucursal activa."""
        self.tree_prods.delete(*self.tree_prods.get_children())
        products = search_products(search_text, only_active=True, sucursal_id=self.sucursal_id)

        for p in products:
            tag = "ok"
            alerta_txt = "Óptimo"

            if p["alerta_vencimiento"]:
                alerta_txt = p["alerta_vencimiento"]
                tag = "warn" if (p["proximo_lote_dias"] or 999) > 30 else "danger"
            elif p["stock_total"] == 0:
                alerta_txt = "Agotado en Sucursal"
                tag = "danger"

            self.tree_prods.insert(
                "",
                "end",
                values=(
                    p["id"],
                    p["codigo_barras"],
                    p["nombre"],
                    f"${p['precio_venta']:.2f}",
                    p["stock_total"],
                    p["proximo_lote_numero"],
                    p["proximo_lote_vence"],
                    alerta_txt
                ),
                tags=(tag,)
            )

    def _handle_search(self):
        term = self.entry_search.get().strip()
        self._load_catalog(term)

    def _on_search_enter(self):
        """Si el texto coincide con un código de barras, lo agrega de inmediato validando stock en sucursal."""
        term = self.entry_search.get().strip()
        if not term:
            return

        prod = get_product_by_barcode(term, sucursal_id=self.sucursal_id)
        if prod:
            qty = 1
            try:
                qty = int(self.entry_qty.get().strip())
                if qty <= 0:
                    qty = 1
            except Exception:
                qty = 1

            ok, msg = self.cart.add_product(prod, quantity=qty)
            if ok:
                self.entry_search.delete(0, tk.END)
                self.entry_qty.delete(0, tk.END)
                self.entry_qty.insert(0, "1")
                self._update_cart_ui()
                self._load_catalog()
            else:
                messagebox.showwarning("Aviso de Inventario en Sucursal", msg, parent=self)
        else:
            self._handle_search()

    def _add_selected_to_cart(self):
        selected = self.tree_prods.selection()
        if not selected:
            messagebox.showinfo("Seleccionar", "Por favor seleccione un medicamento de la lista.", parent=self)
            return

        item_values = self.tree_prods.item(selected[0], "values")
        product_id = int(item_values[0])

        try:
            qty = int(self.entry_qty.get().strip())
            if qty <= 0:
                qty = 1
        except Exception:
            qty = 1

        products = search_products("", only_active=True, sucursal_id=self.sucursal_id)
        target = next((p for p in products if p["id"] == product_id), None)
        if not target:
            return

        ok, msg = self.cart.add_product(target, quantity=qty)
        if ok:
            self.entry_qty.delete(0, tk.END)
            self.entry_qty.insert(0, "1")
            self._update_cart_ui()
            self._load_catalog(self.entry_search.get().strip())
        else:
            messagebox.showwarning("Atención - Stock", msg, parent=self)

    def _set_cart_item_quantity(self):
        """Permite ingresar directamente la cantidad deseada para el producto seleccionado en el carrito."""
        selected = self.tree_cart.selection()
        if not selected:
            messagebox.showinfo("Seleccionar", "Seleccione un medicamento del carrito para modificar su cantidad.", parent=self)
            return
        item_idx = self.tree_cart.index(selected[0])
        cart_items = list(self.cart.items.values())
        if 0 <= item_idx < len(cart_items):
            item = cart_items[item_idx]
            new_qty = simpledialog.askinteger(
                "Modificar Cantidad",
                f"Ingrese la nueva cantidad para '{item.nombre}':",
                parent=self,
                initialvalue=item.cantidad,
                minvalue=1,
                maxvalue=9999
            )
            if new_qty is not None:
                ok, msg = self.cart.update_quantity(item.producto_id, new_qty)
                if ok:
                    self._update_cart_ui()
                else:
                    messagebox.showwarning("Stock Insuficiente", msg, parent=self)

    def _increase_cart_item(self):
        selected = self.tree_cart.selection()
        if not selected:
            return
        item_idx = self.tree_cart.index(selected[0])
        cart_items = list(self.cart.items.values())
        if 0 <= item_idx < len(cart_items):
            item = cart_items[item_idx]
            ok, msg = self.cart.update_quantity(item.producto_id, item.cantidad + 1)
            if ok:
                self._update_cart_ui()
            else:
                messagebox.showwarning("Stock Insuficiente", msg, parent=self)

    def _decrease_cart_item(self):
        selected = self.tree_cart.selection()
        if not selected:
            return
        item_idx = self.tree_cart.index(selected[0])
        cart_items = list(self.cart.items.values())
        if 0 <= item_idx < len(cart_items):
            item = cart_items[item_idx]
            self.cart.update_quantity(item.producto_id, item.cantidad - 1)
            self._update_cart_ui()

    def _remove_cart_item(self):
        selected = self.tree_cart.selection()
        if not selected:
            return
        item_idx = self.tree_cart.index(selected[0])
        cart_items = list(self.cart.items.values())
        if 0 <= item_idx < len(cart_items):
            item = cart_items[item_idx]
            self.cart.remove_product(item.producto_id)
            self._update_cart_ui()
            self._load_catalog(self.entry_search.get().strip())

    def _clear_cart(self):
        if not self.cart.items:
            return
        if messagebox.askyesno("Vaciar Carrito", "¿Desea quitar todos los productos del carrito?", parent=self):
            self.cart.clear()
            self._update_cart_ui()
            self._load_catalog(self.entry_search.get().strip())

    def _update_cart_ui(self):
        self.tree_cart.delete(*self.tree_cart.get_children())
        alerts = []

        for item in self.cart.get_items_list():
            self.tree_cart.insert(
                "",
                "end",
                values=(
                    item["nombre"],
                    item["lote"],
                    item["cantidad"],
                    f"${item['precio']:.2f}",
                    f"${item['subtotal']:.2f}"
                )
            )
            if item.get("alerta"):
                alerts.append(f"⚠️ {item['nombre']}: {item['alerta']}")

        # Actualizar subtotales y total
        self.lbl_subtotal.configure(text=f"${self.cart.subtotal:.2f}")
        self.lbl_iva.configure(text=f"${self.cart.impuesto:.2f}")
        self.lbl_total.configure(text=f"${self.cart.total:.2f}")

        # Mensajes FEFO
        if alerts:
            self.lbl_fefo_alert.configure(text="\n".join(alerts))
        else:
            self.lbl_fefo_alert.configure(text="")

        self._calculate_change()

    def _on_payment_method_change(self):
        metodo = self.combo_metodo.get()
        if metodo != "Efectivo":
            # Si es tarjeta o transferencia, el recibido es el total exacto
            self.entry_recibido.delete(0, tk.END)
            self.entry_recibido.insert(0, f"{self.cart.total:.2f}")
            self.lbl_cambio.configure(text="$0.00")
        else:
            self._calculate_change()

    def _calculate_change(self):
        total = float(self.cart.total)
        try:
            recibido = float(self.entry_recibido.get().strip() or "0")
            cambio = recibido - total
            if cambio >= 0:
                self.lbl_cambio.configure(text=f"${cambio:.2f}", fg=COLOR_SUCCESS)
            else:
                self.lbl_cambio.configure(text=f"-${abs(cambio):.2f}", fg=COLOR_DANGER)
        except ValueError:
            self.lbl_cambio.configure(text="$0.00", fg=COLOR_TEXT_MUTED)

    def _handle_checkout(self):
        if not self.cart.items:
            messagebox.showwarning("Carrito Vacío", "No hay medicamentos en el carrito para cobrar.", parent=self)
            return

        total = float(self.cart.total)
        metodo = self.combo_metodo.get()

        try:
            monto_recibido = float(self.entry_recibido.get().strip() or str(total))
        except ValueError:
            messagebox.showerror("Error", "Ingrese un monto recibido válido.", parent=self)
            return

        if metodo == "Efectivo" and monto_recibido < total:
            messagebox.showwarning(
                "Pago Insuficiente",
                f"El monto recibido (${monto_recibido:.2f}) es menor al total (${total:.2f}).",
                parent=self
            )
            return

        cliente = self.entry_cliente.get().strip() or "Público General"
        current_user = get_current_user()
        user_id = current_user.id if current_user else 1

        # Procesar Venta con Descuento FEFO en la sucursal activa
        success, msg, ticket_data = process_sale(
            cart=self.cart,
            user_id=user_id,
            sucursal_id=self.sucursal_id,
            metodo_pago=metodo,
            monto_recibido=monto_recibido,
            cliente_nombre=cliente
        )

        if success and ticket_data:
            self.last_sale_ticket = ticket_data
            self._update_cart_ui()
            self._load_catalog()
            self.entry_recibido.delete(0, tk.END)
            self.entry_cliente.delete(0, tk.END)
            self.entry_cliente.insert(0, "Público General")

            # Desplegar modal interactivo del ticket
            show_ticket_modal(self.winfo_toplevel(), ticket_data)
        else:
            messagebox.showerror("Error al Cobrar", f"No se pudo completar la venta:\n{msg}", parent=self)

    def _show_last_ticket(self):
        if self.last_sale_ticket:
            show_ticket_modal(self.winfo_toplevel(), self.last_sale_ticket)
        else:
            messagebox.showinfo("Ticket", "No hay ninguna venta reciente en esta sesión.", parent=self)

    def _show_change_branch_modal(self):
        """Permite al empleado o cajero cambiar de sucursal de trabajo."""
        sucursales = list_branches(only_active=True)
        if not sucursales:
            return

        modal = tk.Toplevel(self)
        modal.title("Cambiar Sucursal de Trabajo")
        modal.geometry("380x240")
        modal.configure(bg=COLOR_BG)
        modal.transient(self)
        modal.grab_set()

        hdr = tk.Frame(modal, bg=COLOR_PRIMARY, padx=15, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🏪 Seleccionar Sucursal", font=FONT_TITLE, bg=COLOR_PRIMARY, fg=COLOR_TEXT_WHITE).pack(anchor="w")

        f = tk.Frame(modal, bg=COLOR_BG, padx=20, pady=15)
        f.pack(fill="both", expand=True)

        branch_map = {s["nombre"]: s["id"] for s in sucursales}
        tk.Label(f, text="Sucursal de Caja:", font=FONT_BOLD, bg=COLOR_BG, fg=COLOR_TEXT).pack(anchor="w", pady=(0, 5))

        combo = ttk.Combobox(f, values=list(branch_map.keys()), state="readonly", font=FONT_REGULAR)
        current_name = self.sucursal.nombre if self.sucursal else list(branch_map.keys())[0]
        combo.set(current_name)
        combo.pack(fill="x", pady=(0, 15), ipady=3)

        def apply_change():
            sel = combo.get()
            new_id = branch_map.get(sel)
            if new_id:
                set_current_branch(new_id)
                self.sucursal_id = new_id
                self.sucursal = next((s for s in sucursales if s["id"] == new_id), None)
                self.lbl_branch_badge.configure(text=f"🏪 {sel}")
                self.cart.set_sucursal(new_id)
                self._update_cart_ui()
                self._load_catalog()
                messagebox.showinfo("Sucursal Cambiada", f"Operando ahora en: {sel}\nEl catálogo ha sido actualizado a su stock local.", parent=modal)
                modal.destroy()

        btn_ok = ttk.Button(f, text="Confirmar Cambio", style="Pink.TButton", command=apply_change)
        btn_ok.pack(fill="x", ipady=3)
