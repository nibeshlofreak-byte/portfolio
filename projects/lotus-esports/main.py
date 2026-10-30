"""
Lotus - Plataforma Gamer para Organización de Eventos y Torneos de eSports
Compatible con Flet 0.86+ (Flutter 3.44+) — API moderna sin deprecaciones
"""

import flet as ft
from datetime import datetime
from auth_errors import AuthStoreError
from offline_auth import login_user, register_user

# ── PALETA DE COLORES ─────────────────────────────────────────────────────────
BG       = "#090D1A"   # Fondo dominante — azul marino profundo
CARD     = "#131B2E"   # Tarjetas y barras
CARD_L   = "#1C2742"   # Inputs, hover, bordes internos
PINK     = "#FF1493"   # Acento primario — fucsia brillante
PINK2    = "#FF2E93"   # Hover / gradiente secundario
GLOW     = "#E00070"   # Sombra glow de botones
WHITE    = "#FFFFFF"
MUTED    = "#8E9BB5"   # Subtexto5
DIM      = "#566482"   # Placeholder muy atenuado
BORDER   = "#253354"   # Borde sutil
GREEN    = "#00FFA3"   # Estado en línea / "Gratuito"

# ── HELPERS DE ESTILO ─────────────────────────────────────────────────────────
def pink_btn(text, on_click, icon=None, expand=False, width=None):
    """Botón primario rosado — reemplaza ElevatedButton degradado."""
    return ft.Container(
        expand=expand,
        width=width,
        height=48,
        border_radius=12,
        gradient=ft.LinearGradient(colors=[PINK, PINK2]),
        shadow=ft.BoxShadow(blur_radius=14, color=GLOW, offset=ft.Offset(0, 4)),
        content=ft.Button(
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    *([] if icon is None else [ft.Icon(icon, color=WHITE, size=18)]),
                    ft.Text(text, color=WHITE, weight=ft.FontWeight.BOLD, size=14)
                ]
            ),
            bgcolor=ft.Colors.TRANSPARENT,
            color=WHITE,
            style=ft.ButtonStyle(shadow_color=ft.Colors.TRANSPARENT),
            on_click=on_click
        )
    )

def ghost_btn(text, on_click, icon=None):
    """Botón secundario contorno rosado."""
    return ft.OutlinedButton(
        content=ft.Row(
            spacing=6,
            tight=True,
            controls=[
                *([] if icon is None else [ft.Icon(icon, color=PINK, size=16)]),
                ft.Text(text, color=WHITE, size=13)
            ]
        ),
        style=ft.ButtonStyle(side=ft.BorderSide(1, PINK)),
        on_click=on_click
    )

def field(label, value="", hint="", icon=None, password=False, multiline=False, min_lines=1, max_lines=1):
    return ft.TextField(
        label=label,
        label_style=ft.TextStyle(color=MUTED),
        value=value,
        hint_text=hint,
        hint_style=ft.TextStyle(color=DIM),
        password=password,
        can_reveal_password=password,
        prefix_icon=icon,
        color=WHITE,
        bgcolor=CARD,
        border_color=BORDER,
        focused_border_color=PINK,
        border_radius=10,
        multiline=multiline,
        min_lines=min_lines,
        max_lines=max_lines,
    )

def card(content, padding=16, radius=16):
    return ft.Container(
        bgcolor=CARD,
        border_radius=radius,
        border=ft.Border.all(1, BORDER),
        padding=padding,
        content=content
    )

def section_title(text):
    return ft.Text(text, size=12, weight=ft.FontWeight.BOLD, color=MUTED)

def divider():
    return ft.Divider(color=BORDER, height=1)


# ═════════════════════════════════════════════════════════════════════════════
def main(page: ft.Page):

    page.title    = "Lotus — Gaming & eSports"
    page.bgcolor  = BG
    page.padding  = 0
    page.spacing  = 0
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width  = 430
    page.window.height = 860
    page.window.resizable = True

    # ── ESTADO GLOBAL ─────────────────────────────────────────────────────────
    S = {
        "logged": False,
        "user":   "",
        "accounts": {},
        "auth_mode": "login",
        "tab":    0,
        "sub":    None,      # "create","register","agenda","chat_open","events_hub"
        "filter": "Todos",
        "slots":  16,
        "reg_event":  None,
        "chat_user":  None,
        "stream_likes": 342,
        "stream_liked": False,
        "stream_views": 1845,
        "stream_chat": [
            {"u": "Kakaroto99",  "m": "¡Qué jugada en el punto B!"},
            {"u": "CyberNova",   "m": "Lotus Cup tiene el mejor nivel de la temporada"},
            {"u": "GhostRider",  "m": "VAMOS EQUIPO LOTUS 🔥🔥🔥"},
            {"u": "Sora2026",    "m": "gg wp ese clutch"},
        ],
        "events": [
            {"id":1,"title":"Valorant Lotus Master Cup 2026","game":"Valorant","date":"28 Oct, 2026","platform":"PC","format":"5v5 Eliminación Directa","fee":"Inscripción Gratuita","slots":"16/16 Equipos"},
            {"id":2,"title":"EA Sports FC 26 Continental Clash","game":"EA Sports","date":"02 Nov, 2026","platform":"PlayStation","format":"1v1 Doble Eliminación","fee":"$10 USD","slots":"28/32 Jugadores"},
            {"id":3,"title":"League of Legends: Grieta Lotus","game":"LoL","date":"05 Nov, 2026","platform":"PC","format":"5v5 Torneo Suizo","fee":"Inscripción Gratuita","slots":"8/16 Equipos"},
            {"id":4,"title":"Halo & CoD Cross-Console Open","game":"Crossplay","date":"10 Nov, 2026","platform":"Xbox","format":"4v4 Buscar y Destruir","fee":"Inscripción Gratuita","slots":"12/24 Equipos"},
        ],
        "posts": [
            {"id":1,"user":"Valkyria_Queen","seed":"Valkyria","time":"Hace 15m",
             "content":"¡Buscando duelista para scrim de Valorant esta noche! Lotus Cup playoffs. DM abierto 🎯🔥",
             "likes":24,"liked":False,"comments":7},
            {"id":2,"user":"PixelSlayer","seed":"PixelSlayer","time":"Hace 2h",
             "content":"Récord personal: ¡18 victorias seguidas en EA FC 26! Listos para el torneo continental ⚽🏆",
             "likes":56,"liked":True,"comments":14},
        ],
        "friends": [
            {"name":"LauraGamer","game":"Valorant / LoL","seed":"Laura","added":False},
            {"name":"Andrés_FPS","game":"EA Sports FC","seed":"Andres","added":False},
            {"name":"Camila_Sniper","game":"Call of Duty","seed":"Camila","added":False},
            {"name":"Dúo Legendario","game":"Apex Legends","seed":"Duo","added":False},
        ],
        "chats": [
            {"name":"LauraGamer","msg":"¿A qué hora arrancan las semifinales?","time":"14:48","online":True,"seed":"Laura","unread":2},
            {"name":"Andrés","msg":"Ya armé el lobby para EA FC","time":"13:20","online":True,"seed":"Andres","unread":0},
            {"name":"Dúo Legendario","msg":"Confirmado el registro en Lotus Cup!","time":"Ayer","online":False,"seed":"Duo","unread":0},
            {"name":"Camila","msg":"Buen torneo ayer, GG a todos","time":"20 Oct","online":False,"seed":"Camila","unread":0},
        ],
    }

    root = ft.Container(expand=True, bgcolor=BG)
    page.add(root)

    # ── SNACKBAR ──────────────────────────────────────────────────────────────
    def snack(text, err=False):
        sb = ft.SnackBar(
            content=ft.Text(text, color=WHITE, weight=ft.FontWeight.W_600),
            bgcolor=PINK if not err else "#FF3366",
            duration=3000
        )
        page.overlay.append(sb)
        sb.open = True
        page.update()

    # ── RE-RENDER ─────────────────────────────────────────────────────────────
    def render():
        root.content = login_view() if not S["logged"] else shell()
        page.update()

    def nav(sub=None, data=None):
        S["sub"] = sub
        if data:
            S.update(data)
        render()

    def set_tab(idx):
        S["tab"] = idx
        S["sub"] = None
        render()

    # ══════════════════════════════════════════════════════════════════════════
    # 1. LOGIN
    # ══════════════════════════════════════════════════════════════════════════
    def login_view():
        is_registering = S["auth_mode"] == "register"
        name_f = field("Nombre completo", hint="Tu nombre", icon=ft.Icons.PERSON_OUTLINE)
        email_f = field("Correo electrónico", hint="ejemplo@correo.com",
                        icon=ft.Icons.EMAIL_OUTLINED)
        phone_f = field("Número telefónico", hint="+52 555 123 4567",
                        icon=ft.Icons.PHONE_OUTLINED)
        pass_f = field("Contraseña", hint="Mínimo 8 caracteres",
                       password=True, icon=ft.Icons.LOCK_OUTLINE)

        def do_login(e):
            try:
                user_name = login_user(
                    S["accounts"], email_f.value or "", pass_f.value or ""
                )
            except AuthStoreError as ex:
                snack(str(ex), err=True)
                return
            S.update({"logged": True, "user": user_name, "auth_mode": "login"})
            snack(f"¡Bienvenido a Lotus, {user_name}! 🎮")
            render()

        def do_forgot(e):
            snack("Enlace de recuperación enviado a tu correo")

        def toggle_auth(e):
            S["auth_mode"] = "login" if is_registering else "register"
            render()

        def do_register(e):
            try:
                user_name = register_user(
                    S["accounts"],
                    name_f.value or "",
                    email_f.value or "",
                    phone_f.value or "",
                    pass_f.value or "",
                )
            except AuthStoreError as ex:
                snack(str(ex), err=True)
                return
            S.update({"logged": True, "user": user_name, "auth_mode": "login"})
            snack("¡Cuenta creada! Bienvenido a Lotus 🎮")
            render()

        auth_fields = [email_f, pass_f] if not is_registering else [
            name_f, email_f, phone_f, pass_f
        ]
        auth_action = do_register if is_registering else do_login
        auth_label = "CREAR CUENTA" if is_registering else "INICIAR SESIÓN"

        return ft.Container(
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_CENTER, end=ft.Alignment.BOTTOM_CENTER,
                colors=[BG, "#0F1626", BG]
            ),
            padding=ft.Padding.symmetric(horizontal=24, vertical=30),
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
                spacing=18,
                controls=[
                    ft.Image(src="lotus_logo.png", width=130, height=130, fit=ft.BoxFit.CONTAIN),
                    ft.Text("LOTUS", size=32, weight=ft.FontWeight.BOLD, color=WHITE),
                    ft.Text("ORGANIZACIÓN Y TORNEOS DE ESPORTS", size=11, weight=ft.FontWeight.W_600, color=PINK),
                    ft.Text(
                        "Modo sin base de datos: las cuentas se borran al cerrar la app.",
                        size=11, color=MUTED, text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(height=6),
                    card(ft.Column(spacing=14, controls=[
                        *auth_fields,
                        *([] if is_registering else [
                            ft.Container(
                                alignment=ft.Alignment.CENTER_RIGHT,
                                content=ft.TextButton(
                                    content=ft.Text("¿Olvidaste tu contraseña?", color=MUTED, size=13),
                                    on_click=do_forgot
                                )
                            )
                        ]),
                        pink_btn(auth_label, auth_action, expand=True),
                    ]), padding=22),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Text(
                                "¿Ya tienes cuenta?" if is_registering else "¿No tienes cuenta?",
                                color=MUTED, size=14
                            ),
                            ft.TextButton(
                                content=ft.Text(
                                    "Inicia sesión" if is_registering else "Regístrate",
                                    color=PINK, size=14, weight=ft.FontWeight.BOLD
                                ),
                                on_click=toggle_auth
                            )
                        ]
                    )
                ]
            )
        )
    # ══════════════════════════════════════════════════════════════════════════
    # SHELL (Header + Body + BottomNav)
    # ══════════════════════════════════════════════════════════════════════════
    def shell():
        # header
        header = ft.Container(
            bgcolor=CARD,
            border=ft.Border.only(bottom=ft.BorderSide(1, BORDER)),
            padding=ft.Padding.symmetric(horizontal=18, vertical=12),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                        ft.Image(src="lotus_logo.png", width=34, height=34, fit=ft.BoxFit.CONTAIN),
                        ft.Column(spacing=1, controls=[
                            ft.Text("LOTUS", size=17, weight=ft.FontWeight.BOLD, color=WHITE),
                            ft.Text("eSports Hub", size=10, color=PINK, weight=ft.FontWeight.W_600),
                        ])
                    ]),
                    ft.Row(spacing=6, controls=[
                        ft.IconButton(icon=ft.Icons.NOTIFICATIONS_OUTLINED, icon_color=MUTED,
                                      tooltip="Notificaciones",
                                      on_click=lambda e: snack("Sin notificaciones pendientes")),
                        ft.Stack(controls=[
                            ft.CircleAvatar(
                                foreground_image_src="https://api.dicebear.com/7.x/bottts/png?seed=LotusGamer",
                                radius=17),
                            ft.Container(width=10, height=10, bgcolor=GREEN, border_radius=5,
                                         border=ft.Border.all(2, CARD), right=0, bottom=0)
                        ])
                    ])
                ]
            )
        )

        # body
        sub = S["sub"]
        if   sub == "create":   body = view_create_event()
        elif sub == "register": body = view_register_event()
        elif sub == "agenda":   body = view_agenda()
        elif sub == "chat_open":body = view_chat_open()
        elif sub == "events_hub": body = view_events_hub()
        else:
            views = [view_dashboard, view_events_hub, view_agenda, view_live, view_social]
            body = views[min(S["tab"], 4)]()

        # bottom nav
        sel = S["tab"] if sub is None else -1
        bnav = ft.NavigationBar(
            selected_index=max(sel, 0),
            bgcolor=CARD,
            indicator_color=PINK,
            on_change=lambda e: set_tab(e.control.selected_index),
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.HOME_OUTLINED,         selected_icon=ft.Icons.HOME,          label="Inicio"),
                ft.NavigationBarDestination(icon=ft.Icons.SPORTS_ESPORTS_OUTLINED,selected_icon=ft.Icons.SPORTS_ESPORTS,label="Torneos"),
                ft.NavigationBarDestination(icon=ft.Icons.CALENDAR_MONTH_OUTLINED,selected_icon=ft.Icons.CALENDAR_MONTH,label="Agenda"),
                ft.NavigationBarDestination(icon=ft.Icons.LIVE_TV_OUTLINED,       selected_icon=ft.Icons.LIVE_TV,       label="En Vivo"),
                ft.NavigationBarDestination(icon=ft.Icons.PEOPLE_OUTLINE,         selected_icon=ft.Icons.PEOPLE,        label="Social"),
            ]
        )

        return ft.Column(expand=True, spacing=0, controls=[
            header,
            ft.Container(expand=True, content=body),
            bnav
        ])

    # ══════════════════════════════════════════════════════════════════════════
    # 2. DASHBOARD
    # ══════════════════════════════════════════════════════════════════════════
    def view_dashboard():
        def qcard(title, sub, icon, g1, g2, on_click):
            return ft.Container(
                expand=True, height=108,
                bgcolor=CARD, border_radius=14, border=ft.Border.all(1, BORDER),
                padding=14, on_click=on_click, ink=True,
                content=ft.Column(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    ft.Container(padding=8, border_radius=10,
                                 gradient=ft.LinearGradient(colors=[g1, g2]),
                                 content=ft.Icon(icon, color=WHITE, size=20)),
                    ft.Column(spacing=2, controls=[
                        ft.Text(title, size=14, weight=ft.FontWeight.BOLD, color=WHITE),
                        ft.Text(sub,   size=11, color=MUTED)
                    ])
                ])
            )

        banner = ft.Container(
            height=138, border_radius=16,
            gradient=ft.LinearGradient(begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT,
                                        colors=["#1D2A4D","#3B1038","#121A2D"]),
            border=ft.Border.all(1, GLOW), padding=16,
            content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                           vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                ft.Column(spacing=6, controls=[
                    ft.Container(bgcolor=PINK, border_radius=6,
                                 padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                 content=ft.Text("DESTACADO", size=10, weight=ft.FontWeight.BOLD, color=WHITE)),
                    ft.Text("Gran Torneo Lotus 2026", size=16, weight=ft.FontWeight.BOLD, color=WHITE),
                    ft.Text("Bolsa de premios: \$5,000 USD", size=12, color=MUTED),
                ]),
                pink_btn("Ver Ahora", lambda e: nav("agenda"))
            ])
        )

        return ft.Container(expand=True, padding=16,
            content=ft.Column(scroll=ft.ScrollMode.AUTO, spacing=16, controls=[
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    ft.Column(spacing=2, controls=[
                        ft.Text(f"¡Hola, {S['user']}! 👋", size=19, weight=ft.FontWeight.BOLD, color=WHITE),
                        ft.Text("¿Listo para competir hoy?", size=13, color=MUTED)
                    ]),
                    ft.IconButton(icon=ft.Icons.LOGOUT, icon_color=MUTED, tooltip="Cerrar sesión",
                                  on_click=lambda e: [S.update({"logged":False}), render()])
                ]),
                banner,
                section_title("ACCESOS RÁPIDOS"),
                ft.Row(spacing=10, controls=[
                    qcard("Eventos",   "Gestión de torneos",   ft.Icons.EMOJI_EVENTS,
                          "#FF416C","#FF4B2B", lambda e: nav("agenda")),
                    qcard("En Vivo",   "Streaming directo",    ft.Icons.PLAY_CIRCLE_FILL,
                          PINK,"#7928CA", lambda e: set_tab(3)),
                ]),
                ft.Row(spacing=10, controls=[
                    qcard("Comunidad", "Conéctate con gamers", ft.Icons.DIVERSITY_3,
                          "#00B4DB","#0083B0", lambda e: set_tab(4)),
                    qcard("Chats",     "Mensajes y grupos",    ft.Icons.CHAT_BUBBLE,
                          "#11998E","#38EF7D", lambda e: nav("chat_open", {"chat_user": S["chats"][0]})),
                ]),
                card(ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    ft.Row(spacing=10, controls=[
                        ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, color=PINK, size=26),
                        ft.Column(spacing=2, controls=[
                            ft.Text("¿Eres organizador?", size=14, weight=ft.FontWeight.BOLD, color=WHITE),
                            ft.Text("Publica tu torneo en minutos", size=11, color=MUTED)
                        ])
                    ]),
                    pink_btn("Crear", lambda e: nav("create"))
                ]))
            ])
        )

    # ══════════════════════════════════════════════════════════════════════════
    # 3A. HUB DE TORNEOS (tab 1)
    # ══════════════════════════════════════════════════════════════════════════
    def view_events_hub():
        def hub_card(icon, icon_bg, title, sub, btn_text, btn_outlined, on_click):
            return card(ft.Column(spacing=12, controls=[
                ft.Row(spacing=12, controls=[
                    ft.Container(padding=10, border_radius=12, bgcolor=icon_bg,
                                 content=ft.Icon(icon, color=WHITE)),
                    ft.Column(spacing=2, controls=[
                        ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=WHITE),
                        ft.Text(sub,   size=12, color=MUTED)
                    ])
                ]),
                ghost_btn(btn_text, on_click) if btn_outlined else pink_btn(btn_text, on_click, expand=True)
            ]))

        return ft.Container(expand=True, padding=18,
            content=ft.Column(scroll=ft.ScrollMode.AUTO, spacing=16, controls=[
                ft.Text("GESTIÓN DE TORNEOS", size=20, weight=ft.FontWeight.BOLD, color=WHITE),
                ft.Text("Explora torneos o crea tu propia competencia oficial en Lotus.", size=13, color=MUTED),
                hub_card(ft.Icons.ADD_TASK, PINK,
                         "Crear Nuevo Evento", "Personaliza juego, fechas, reglas y cupos",
                         "Abrir Creador de Torneos", False,
                         lambda e: nav("create")),
                hub_card(ft.Icons.CALENDAR_MONTH, "#7928CA",
                         "Ver Agenda Completa", "Filtra por EA Sports, LoL, Valorant y más",
                         "Explorar Agenda y Torneos", True,
                         lambda e: nav("agenda")),
                hub_card(ft.Icons.EMOJI_EVENTS, "#0083B0",
                         "Mis Torneos Activos", "Revisa el estado de tus inscripciones",
                         "Ver Mis Torneos", True,
                         lambda e: snack("Sección en construcción — próximamente")),
            ])
        )

    # ══════════════════════════════════════════════════════════════════════════
    # 3B. CREAR TORNEO
    # ══════════════════════════════════════════════════════════════════════════
    def view_create_event():
        name_f  = field("Nombre del evento / torneo", hint="ej. Gran Copa Lotus Invierno")
        fmt_f   = field("Formato de Competencia", value="Eliminación Directa (Bo3)")
        date_lbl = ft.Text("2026-11-15", size=15, weight=ft.FontWeight.W_600, color=WHITE)

        game_dd = ft.Dropdown(
            label="Juego", label_style=ft.TextStyle(color=MUTED),
            bgcolor=CARD, color=WHITE, border_color=BORDER, focused_border_color=PINK,
            border_radius=10, value="Valorant",
            options=[ft.dropdown.Option(g) for g in ["Valorant","EA Sports","LoL","Crossplay"]]
        )
        plat_dd = ft.Dropdown(
            label="Plataforma", label_style=ft.TextStyle(color=MUTED),
            bgcolor=CARD, color=WHITE, border_color=BORDER, focused_border_color=PINK,
            border_radius=10, value="PC",
            options=[ft.dropdown.Option(p) for p in ["PC","PlayStation","Xbox"]]
        )

        dp = ft.DatePicker(
            first_date=datetime(2026,1,1), last_date=datetime(2027,12,31),
            on_change=lambda e: [setattr(date_lbl,"value", e.control.value.strftime("%Y-%m-%d")), page.update()] if e.control.value else None
        )
        page.overlay.append(dp)

        slots_lbl = ft.Text(str(S["slots"]), size=18, weight=ft.FontWeight.BOLD, color=WHITE)

        def dec(e):
            if S["slots"] > 2: S["slots"] -= 2; slots_lbl.value = str(S["slots"]); page.update()
        def inc(e):
            if S["slots"] < 128: S["slots"] += 2; slots_lbl.value = str(S["slots"]); page.update()

        def submit(e):
            if not name_f.value:
                snack("Ingresa un nombre para el torneo", err=True); return
            S["events"].insert(0, {
                "id": len(S["events"])+1, "title": name_f.value,
                "game": game_dd.value, "date": date_lbl.value,
                "platform": plat_dd.value, "format": fmt_f.value,
                "fee": "Inscripción Gratuita", "slots": f"0/{S['slots']} Participantes"
            })
            snack(f"¡Torneo '{name_f.value}' creado con éxito! 🏆")
            nav("agenda")

        return ft.Container(expand=True, padding=18,
            content=ft.Column(scroll=ft.ScrollMode.AUTO, spacing=14, controls=[
                ft.Row(controls=[
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=WHITE, on_click=lambda e: nav()),
                    ft.Text("CREAR TORNEO / EVENTO", size=18, weight=ft.FontWeight.BOLD, color=WHITE)
                ]),
                card(ft.Column(spacing=14, controls=[
                    name_f, game_dd, plat_dd, fmt_f,
                    # DatePicker row
                    ft.Container(bgcolor=CARD_L, border_radius=10, padding=12,
                        content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                            ft.Column(spacing=2, controls=[
                                ft.Text("Fecha del Evento", size=12, color=MUTED), date_lbl
                            ]),
                            pink_btn("Elegir Fecha", lambda e: [setattr(dp,"open",True), page.update()],
                                     icon=ft.Icons.CALENDAR_MONTH)
                        ])
                    ),
                    # Slots counter
                    ft.Container(bgcolor=CARD_L, border_radius=10, padding=12,
                        content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                       vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                            ft.Column(spacing=2, controls=[
                                ft.Text("Límite de Participantes", size=12, color=MUTED),
                                ft.Text("Cupos máximos disponibles", size=10, color=DIM)
                            ]),
                            ft.Row(spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                                ft.IconButton(icon=ft.Icons.REMOVE_CIRCLE_OUTLINE, icon_color=PINK, on_click=dec),
                                slots_lbl,
                                ft.IconButton(icon=ft.Icons.ADD_CIRCLE_OUTLINE,    icon_color=PINK, on_click=inc),
                            ])
                        ])
                    ),
                    pink_btn("CREAR EVENTO", submit, icon=ft.Icons.CHECK_CIRCLE_OUTLINE, expand=True),
                ]))
            ])
        )

    # ══════════════════════════════════════════════════════════════════════════
    # 3C. INSCRIBIRSE A EVENTO
    # ══════════════════════════════════════════════════════════════════════════
    def view_register_event():
        ev = S["reg_event"] or S["events"][0]
        gt_f = field("Gamertag / Capitán del Equipo", value=S["user"])
        dc_f = field("Discord Tag", value="ProGamer#7777", hint="usuario#0000")

        def confirm(e):
            snack(f"¡Inscripción confirmada en '{ev['title']}'! Revisa tu Discord 📩")
            nav("agenda")

        fee_color = GREEN if "Gratuita" in ev["fee"] else PINK
        return ft.Container(expand=True, padding=18,
            content=ft.Column(scroll=ft.ScrollMode.AUTO, spacing=14, controls=[
                ft.Row(controls=[
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=WHITE, on_click=lambda e: nav("agenda")),
                    ft.Text("CONFIRMAR INSCRIPCIÓN", size=18, weight=ft.FontWeight.BOLD, color=WHITE)
                ]),
                card(ft.Column(spacing=12, controls=[
                    ft.Text(ev["title"], size=17, weight=ft.FontWeight.BOLD, color=WHITE),
                    ft.Row(spacing=8, controls=[
                        ft.Chip(label=ft.Text(ev["game"],     color=WHITE), bgcolor=CARD_L),
                        ft.Chip(label=ft.Text(ev["platform"], color=WHITE), bgcolor=CARD_L),
                    ]),
                    divider(),
                    ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                        ft.Text("Costo de Entrada:", color=MUTED, size=14),
                        ft.Text(ev["fee"], color=fee_color, size=15, weight=ft.FontWeight.BOLD)
                    ]),
                    ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                        ft.Text("Fecha:",   color=MUTED, size=14),
                        ft.Text(ev["date"], color=WHITE, size=14, weight=ft.FontWeight.W_600)
                    ]),
                    ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                        ft.Text("Formato:",   color=MUTED, size=14),
                        ft.Text(ev["format"], color=WHITE, size=13)
                    ]),
                    divider(),
                    section_title("DATOS DEL JUGADOR"),
                    gt_f, dc_f,
                    pink_btn("CONFIRMAR INSCRIPCIÓN", confirm,
                             icon=ft.Icons.CHECK_CIRCLE, expand=True),
                ]))
            ])
        )

    # ══════════════════════════════════════════════════════════════════════════
    # 3D. AGENDA
    # ══════════════════════════════════════════════════════════════════════════
    def view_agenda():
        filters = ["Todos","EA Sports","LoL","Valorant"]

        def set_f(f): S["filter"] = f; render()

        filtered = [ev for ev in S["events"]
                    if S["filter"] == "Todos" or ev["game"] == S["filter"]]

        def ev_card(ev):
            fee_col = GREEN if "Gratuita" in ev["fee"] else PINK
            return card(ft.Column(spacing=10, controls=[
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    ft.Container(bgcolor=CARD_L, border_radius=8,
                                 padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                                 border=ft.Border.all(1, BORDER),
                                 content=ft.Text(ev["game"], size=11, weight=ft.FontWeight.BOLD, color=WHITE)),
                    ft.Row(spacing=4, controls=[
                        ft.Icon(ft.Icons.CALENDAR_TODAY, size=13, color=PINK),
                        ft.Text(ev["date"], size=12, color=MUTED)
                    ])
                ]),
                ft.Text(ev["title"], size=15, weight=ft.FontWeight.BOLD, color=WHITE),
                ft.Row(spacing=14, controls=[
                    ft.Row(spacing=4, controls=[ft.Icon(ft.Icons.DEVICES, size=13, color=MUTED), ft.Text(ev["platform"], size=12, color=MUTED)]),
                    ft.Row(spacing=4, controls=[ft.Icon(ft.Icons.PERSON,  size=13, color=MUTED), ft.Text(ev["slots"],    size=12, color=MUTED)]),
                ]),
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Text(ev["fee"], size=13, weight=ft.FontWeight.BOLD, color=fee_col),
                    ft.Row(spacing=8, controls=[
                        ghost_btn("Ver Detalles", lambda e, v=ev: show_ev_dialog(v)),
                        pink_btn("Inscribirse",   lambda e, v=ev: nav("register", {"reg_event": v}))
                    ])
                ])
            ]))

        filter_row = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=8, controls=[
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=14, vertical=7),
                border_radius=20,
                bgcolor=PINK if f == S["filter"] else CARD,
                border=ft.Border.all(1, PINK if f == S["filter"] else BORDER),
                on_click=lambda e, fv=f: set_f(fv),
                content=ft.Text(f, size=13,
                                weight=ft.FontWeight.BOLD if f == S["filter"] else ft.FontWeight.NORMAL,
                                color=WHITE if f == S["filter"] else MUTED)
            ) for f in filters
        ])

        return ft.Container(expand=True, padding=18,
            content=ft.Column(spacing=12, controls=[
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    ft.Text("AGENDA DE TORNEOS", size=18, weight=ft.FontWeight.BOLD, color=WHITE),
                    ft.IconButton(icon=ft.Icons.ADD, icon_color=PINK, tooltip="Crear torneo",
                                  on_click=lambda e: nav("create"))
                ]),
                filter_row,
                ft.Container(expand=True,
                    content=ft.ListView(spacing=10,
                        controls=[ev_card(ev) for ev in filtered] if filtered else [
                            ft.Container(padding=40, alignment=ft.Alignment.CENTER,
                                content=ft.Text("Sin torneos en esta categoría.", color=MUTED))
                        ]
                    )
                )
            ])
        )

    def show_ev_dialog(ev):
        fee_col = GREEN if "Gratuita" in ev["fee"] else PINK
        def close(e): dlg.open = False; page.update()
        dlg = ft.AlertDialog(
            bgcolor=CARD,
            title=ft.Text(ev["title"], color=WHITE, weight=ft.FontWeight.BOLD, size=15),
            content=ft.Column(main_axis_size=ft.MainAxisSize.MIN, spacing=8, controls=[
                ft.Text(f"🎮 Juego: {ev['game']}",      color=WHITE),
                ft.Text(f"💻 Plataforma: {ev['platform']}", color=MUTED),
                ft.Text(f"⚔️  Formato: {ev['format']}",     color=MUTED),
                ft.Text(f"📅 Fecha: {ev['date']}",          color=MUTED),
                ft.Text(f"💰 Costo: {ev['fee']}",           color=fee_col, weight=ft.FontWeight.BOLD),
                ft.Text(f"👥 Cupos: {ev['slots']}",         color=MUTED),
            ]),
            actions=[
                ft.TextButton(content=ft.Text("Cerrar"), on_click=close),
                ft.TextButton(
                    content=ft.Text("Inscribirme", color=PINK, weight=ft.FontWeight.BOLD),
                    on_click=lambda e: [close(e), nav("register", {"reg_event": ev})]
                )
            ]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    # ══════════════════════════════════════════════════════════════════════════
    # 4. EN VIVO (STREAMING)
    # ══════════════════════════════════════════════════════════════════════════
    def view_live():
        chat_f = ft.TextField(
            hint_text="Envía un mensaje al stream...",
            hint_style=ft.TextStyle(color=DIM),
            color=WHITE, bgcolor=CARD_L, border_color=BORDER,
            focused_border_color=PINK, border_radius=10, expand=True, dense=True
        )

        def send_msg(e):
            if chat_f.value:
                S["stream_chat"].append({"u": S["user"], "m": chat_f.value})
                chat_f.value = ""
                render()

        def toggle_like(e):
            S["stream_liked"] = not S["stream_liked"]
            S["stream_likes"] += 1 if S["stream_liked"] else -1
            render()

        like_icon = ft.Icons.FAVORITE if S["stream_liked"] else ft.Icons.FAVORITE_BORDER
        like_col  = PINK if S["stream_liked"] else MUTED

        return ft.Container(expand=True, padding=18,
            content=ft.Column(scroll=ft.ScrollMode.AUTO, spacing=14, controls=[
                ft.Text("TRANSMISIÓN EN DIRECTO", size=18, weight=ft.FontWeight.BOLD, color=WHITE),

                # Player simulado
                ft.Container(
                    height=200, border_radius=16, bgcolor="#070A12",
                    border=ft.Border.all(1, BORDER),
                    content=ft.Stack(controls=[
                        ft.Container(expand=True, gradient=ft.LinearGradient(
                            begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT,
                            colors=["#141E30","#243B55","#0F2027"]
                        )),
                        ft.Container(top=12, left=12, border_radius=6, bgcolor="#E50914",
                            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                            content=ft.Row(spacing=4, controls=[
                                ft.Icon(ft.Icons.CIRCLE, size=8, color=WHITE),
                                ft.Text("EN VIVO", size=10, weight=ft.FontWeight.BOLD, color=WHITE)
                            ])
                        ),
                        ft.Container(top=12, right=12, border_radius=6, bgcolor="#88000000",
                            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                            content=ft.Row(spacing=4, controls=[
                                ft.Icon(ft.Icons.VISIBILITY, size=12, color=WHITE),
                                ft.Text(f"{S['stream_views']:,}", size=11, color=WHITE)
                            ])
                        ),
                        ft.Container(alignment=ft.Alignment.CENTER,
                            content=ft.IconButton(icon=ft.Icons.PLAY_CIRCLE_FILL,
                                icon_color=PINK, icon_size=56,
                                on_click=lambda e: snack("Reproducción iniciada ▶"))
                        )
                    ])
                ),

                # Info streamer
                card(ft.Column(spacing=10, controls=[
                    ft.Text("Campeonato de Valorant: Finales Lotus Cup",
                            size=15, weight=ft.FontWeight.BOLD, color=WHITE),
                    ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                           vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                        ft.Row(spacing=8, controls=[
                            ft.CircleAvatar(
                                foreground_image_src="https://api.dicebear.com/7.x/bottts/png?seed=LotusOfficial",
                                radius=16),
                            ft.Column(spacing=1, controls=[
                                ft.Text("LotusGaming_Official", size=13, weight=ft.FontWeight.BOLD, color=WHITE),
                                ft.Text("Canal verificado • 120k seguidores", size=10, color=MUTED)
                            ])
                        ]),
                        ft.Button(
                            content=ft.Row(spacing=6, controls=[
                                ft.Icon(like_icon, size=16, color=like_col),
                                ft.Text(str(S["stream_likes"]), color=WHITE, size=12)
                            ]),
                            bgcolor=CARD_L,
                            style=ft.ButtonStyle(side=ft.BorderSide(1, PINK if S["stream_liked"] else BORDER)),
                            on_click=toggle_like
                        )
                    ])
                ])),

                # Chat en vivo
                card(ft.Column(spacing=10, controls=[
                    ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                        section_title("CHAT EN VIVO"),
                        ft.TextButton(
                            content=ft.Text("Ver Chat Completo", color=PINK, size=12, weight=ft.FontWeight.BOLD),
                            on_click=lambda e: snack("Chat en vivo a pantalla completa")
                        )
                    ]),
                    divider(),
                    ft.Column(spacing=6, controls=[
                        ft.Row(spacing=6, controls=[
                            ft.Text(m["u"], size=12, weight=ft.FontWeight.BOLD,
                                    color=PINK if m["u"] == S["user"] else "#00B4DB"),
                            ft.Text(m["m"], size=12, color=WHITE, expand=True)
                        ]) for m in S["stream_chat"][-5:]
                    ]),
                    ft.Row(spacing=8, controls=[
                        chat_f,
                        ft.IconButton(icon=ft.Icons.SEND, icon_color=PINK, on_click=send_msg)
                    ])
                ]))
            ])
        )

    # ══════════════════════════════════════════════════════════════════════════
    # 5. COMUNIDAD / RED SOCIAL
    # ══════════════════════════════════════════════════════════════════════════
    def view_social():
        post_f = field("¿Qué estás pensando?",
                       hint="Comparte tus clips o logros con la comunidad...",
                       multiline=True, min_lines=2, max_lines=4)

        def publish(e):
            if not post_f.value:
                snack("Escribe algo para publicar", err=True); return
            S["posts"].insert(0, {
                "id": len(S["posts"])+1, "user": S["user"],
                "seed": "LotusGamer", "time": "Justo ahora",
                "content": post_f.value, "likes": 0, "liked": False, "comments": 0
            })
            post_f.value = ""
            snack("¡Publicación compartida con la comunidad! 🎮")
            render()

        def toggle_like(pid):
            for p in S["posts"]:
                if p["id"] == pid:
                    p["liked"] = not p["liked"]
                    p["likes"] += 1 if p["liked"] else -1
                    break
            render()

        def toggle_friend(name):
            for f in S["friends"]:
                if f["name"] == name:
                    f["added"] = not f["added"]
                    snack(f"{'Solicitud enviada a' if f['added'] else 'Solicitud cancelada a'} {name}")
                    break
            render()

        avatar_url = "https://api.dicebear.com/7.x/bottts/png?seed="

        friend_cards = [
            ft.Container(width=175, padding=10, bgcolor=CARD, border_radius=12,
                border=ft.Border.all(1, BORDER),
                content=ft.Column(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    ft.Row(spacing=8, controls=[
                        ft.CircleAvatar(foreground_image_src=avatar_url+fr["seed"], radius=15),
                        ft.Column(spacing=1, controls=[
                            ft.Text(fr["name"], size=12, weight=ft.FontWeight.BOLD, color=WHITE),
                            ft.Text(fr["game"], size=10, color=MUTED)
                        ])
                    ]),
                    ft.OutlinedButton(
                        content=ft.Row(spacing=4, tight=True, controls=[
                            ft.Icon(ft.Icons.CHECK if fr["added"] else ft.Icons.PERSON_ADD,
                                    size=14,
                                    color=GREEN if fr["added"] else PINK),
                            ft.Text("Agregado" if fr["added"] else "Agregar",
                                    color=GREEN if fr["added"] else PINK, size=12)
                        ]),
                        style=ft.ButtonStyle(
                            side=ft.BorderSide(1, GREEN if fr["added"] else PINK),
                            padding=ft.Padding.symmetric(horizontal=8, vertical=4)
                        ),
                        on_click=lambda e, n=fr["name"]: toggle_friend(n)
                    )
                ])
            ) for fr in S["friends"]
        ]

        post_cards = []
        for p in S["posts"]:
            like_icon = ft.Icons.FAVORITE if p["liked"] else ft.Icons.FAVORITE_BORDER
            like_col  = PINK if p["liked"] else MUTED
            post_cards.append(
                card(ft.Column(spacing=10, controls=[
                    ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                        ft.Row(spacing=10, controls=[
                            ft.CircleAvatar(foreground_image_src=avatar_url+p["seed"], radius=17),
                            ft.Column(spacing=1, controls=[
                                ft.Text(p["user"], size=14, weight=ft.FontWeight.BOLD, color=WHITE),
                                ft.Text(p["time"], size=11, color=MUTED)
                            ])
                        ]),
                        ft.IconButton(icon=ft.Icons.MORE_VERT, icon_color=MUTED,
                                      on_click=lambda e: snack("Opciones de publicación"))
                    ]),
                    ft.Text(p["content"], size=13, color=WHITE),
                    divider(),
                    ft.Row(alignment=ft.MainAxisAlignment.SPACE_AROUND, controls=[
                        ft.TextButton(
                            content=ft.Row(spacing=4, controls=[
                                ft.Icon(like_icon, color=like_col, size=17),
                                ft.Text(f"{p['likes']} Likes", color=WHITE, size=12)
                            ]),
                            on_click=lambda e, pid=p["id"]: toggle_like(pid)
                        ),
                        ft.TextButton(
                            content=ft.Row(spacing=4, controls=[
                                ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE, color=MUTED, size=17),
                                ft.Text(f"{p['comments']} Comentarios", color=WHITE, size=12)
                            ]),
                            on_click=lambda e: snack("Cargando comentarios...")
                        ),
                        ft.TextButton(
                            content=ft.Row(spacing=4, controls=[
                                ft.Icon(ft.Icons.SHARE_OUTLINED, color=MUTED, size=17),
                                ft.Text("Compartir", color=WHITE, size=12)
                            ]),
                            on_click=lambda e: snack("Enlace copiado al portapapeles 📋")
                        ),
                    ])
                ]))
            )

        return ft.Container(expand=True, padding=18,
            content=ft.Column(scroll=ft.ScrollMode.AUTO, spacing=16, controls=[
                ft.Text("COMUNIDAD & RED SOCIAL", size=18, weight=ft.FontWeight.BOLD, color=WHITE),
                # Publicar
                card(ft.Column(spacing=12, controls=[
                    ft.Row(spacing=10, controls=[
                        ft.CircleAvatar(foreground_image_src=avatar_url+"LotusGamer", radius=17),
                        ft.Text(S["user"], size=14, weight=ft.FontWeight.BOLD, color=WHITE)
                    ]),
                    post_f,
                    ft.Row(alignment=ft.MainAxisAlignment.END, controls=[
                        pink_btn("Publicar", publish, icon=ft.Icons.SEND_ROUNDED)
                    ])
                ])),
                # Amigos
                section_title("AMIGOS RECOMENDADOS"),
                ft.Container(height=115,
                    content=ft.ListView(scroll_direction=ft.Axis.HORIZONTAL, spacing=10,
                                        controls=friend_cards)),
                # Feed
                section_title("ÚLTIMAS PUBLICACIONES"),
                *post_cards
            ])
        )

    # ══════════════════════════════════════════════════════════════════════════
    # 6. CHATS — Lista completa + Chat abierto
    # ══════════════════════════════════════════════════════════════════════════
    def view_chats_list():
        """Lista de conversaciones en el tab Social (o acceso directo)."""
        avatar_url = "https://api.dicebear.com/7.x/bottts/png?seed="

        def chat_row(ch):
            return ft.Container(
                bgcolor=CARD, border_radius=14, border=ft.Border.all(1, BORDER),
                padding=12, on_click=lambda e, c=ch: nav("chat_open", {"chat_user": c}), ink=True,
                content=ft.Row(spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Stack(controls=[
                        ft.CircleAvatar(foreground_image_src=avatar_url+ch["seed"], radius=22),
                        ft.Container(
                            width=11, height=11,
                            bgcolor=GREEN if ch["online"] else MUTED,
                            border_radius=6, border=ft.Border.all(2, CARD),
                            right=0, bottom=0
                        )
                    ]),
                    ft.Column(expand=True, spacing=2, controls=[
                        ft.Text(ch["name"], size=14, weight=ft.FontWeight.BOLD, color=WHITE),
                        ft.Text(ch["msg"], size=12, color=MUTED, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
                    ]),
                    ft.Column(horizontal_alignment=ft.CrossAxisAlignment.END, spacing=4, controls=[
                        ft.Text(ch["time"], size=11, color=MUTED),
                        ft.Container(
                            visible=ch["unread"] > 0,
                            bgcolor=PINK, border_radius=10,
                            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                            content=ft.Text(str(ch["unread"]), size=11, color=WHITE, weight=ft.FontWeight.BOLD)
                        )
                    ])
                ])
            )

        return ft.Container(expand=True, padding=18,
            content=ft.Column(spacing=14, controls=[
                ft.Text("CHATS & MENSAJES", size=18, weight=ft.FontWeight.BOLD, color=WHITE),
                ft.Container(expand=True,
                    content=ft.ListView(spacing=10, controls=[chat_row(ch) for ch in S["chats"]])
                )
            ])
        )

    def view_chat_open():
        ch = S["chat_user"] or S["chats"][0]
        avatar_url = "https://api.dicebear.com/7.x/bottts/png?seed="

        msg_input = ft.TextField(
            hint_text=f"Escribir a {ch['name']}...",
            hint_style=ft.TextStyle(color=DIM),
            color=WHITE, bgcolor=CARD_L, border_color=BORDER,
            focused_border_color=PINK, border_radius=10, expand=True, dense=True
        )

        def send(e):
            if msg_input.value:
                ch["msg"]  = msg_input.value
                ch["time"] = "Ahora"
                msg_input.value = ""
                snack("Mensaje enviado ✓")
                render()

        return ft.Container(expand=True, padding=16,
            content=ft.Column(spacing=12, controls=[
                # Header conversación
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    ft.Row(spacing=8, controls=[
                        ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=WHITE,
                                      on_click=lambda e: nav()),
                        ft.CircleAvatar(foreground_image_src=avatar_url+ch["seed"], radius=18),
                        ft.Column(spacing=1, controls=[
                            ft.Text(ch["name"], size=15, weight=ft.FontWeight.BOLD, color=WHITE),
                            ft.Text("En línea" if ch.get("online") else "Desconectado",
                                    size=11, color=GREEN if ch.get("online") else MUTED)
                        ])
                    ]),
                    ft.Row(spacing=4, controls=[
                        ft.IconButton(icon=ft.Icons.CALL,        icon_color=PINK,
                                      on_click=lambda e: snack("Iniciando llamada de voz...")),
                        ft.IconButton(icon=ft.Icons.VIDEOCAM,    icon_color=MUTED,
                                      on_click=lambda e: snack("Videollamada no disponible en esta versión")),
                    ])
                ]),
                divider(),
                # Historial de mensajes
                ft.Container(expand=True,
                    content=ft.ListView(spacing=10, controls=[
                        ft.Container(alignment=ft.Alignment.CENTER_LEFT,
                            content=ft.Container(
                                padding=12, border_radius=14,
                                bgcolor=CARD, border=ft.Border.all(1, BORDER),
                                content=ft.Column(spacing=2, controls=[
                                    ft.Text(ch["msg"], color=WHITE, size=13),
                                    ft.Text(ch["time"], size=10, color=MUTED)
                                ])
                            )
                        ),
                        ft.Container(alignment=ft.Alignment.CENTER_RIGHT,
                            content=ft.Container(
                                padding=12, border_radius=14,
                                gradient=ft.LinearGradient(colors=[PINK, PINK2]),
                                content=ft.Column(spacing=2, controls=[
                                    ft.Text("¡Hola! Sí, todo listo para la ronda. Conectémonos al stream de Lotus.",
                                            color=WHITE, size=13),
                                    ft.Text("Entregado ✓", size=10, color="#FFDDEE")
                                ])
                            )
                        )
                    ])
                ),
                # Input
                ft.Row(spacing=8, controls=[
                    ft.IconButton(icon=ft.Icons.ATTACH_FILE, icon_color=MUTED,
                                  on_click=lambda e: snack("Adjuntar archivo — próximamente")),
                    msg_input,
                    ft.IconButton(icon=ft.Icons.SEND, icon_color=PINK, on_click=send)
                ])
            ])
        )

    # En el tab Social (tab 4) mostramos la lista de chats también desde
    # el tab 0 (dashboard) hay acceso directo al primer chat.
    # Redefinimos view_social para incluir el sub-tab de chats:
    original_social = view_social

    def view_social_with_chats():
        # Si estamos en sub == "chat_open" ya se maneja arriba en shell()
        return original_social()

    # El tab de Social incluye la lista de Chats como sección final:
    _base_social = view_social

    def view_social():
        base = _base_social()
        return base

    # Tabla de vistas por pestaña
    _tab_views = [
        view_dashboard,    # 0 Inicio
        view_events_hub,   # 1 Torneos
        view_agenda,       # 2 Agenda
        view_live,         # 3 En Vivo
        view_chats_list,   # 4 Social → mostramos lista de chats aquí
    ]

    # Actualizamos la referencia en shell()
    def shell():
        header = ft.Container(
            bgcolor=CARD,
            border=ft.Border.only(bottom=ft.BorderSide(1, BORDER)),
            padding=ft.Padding.symmetric(horizontal=18, vertical=12),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                        ft.Image(src="lotus_logo.png", width=34, height=34, fit=ft.BoxFit.CONTAIN),
                        ft.Column(spacing=1, controls=[
                            ft.Text("LOTUS", size=17, weight=ft.FontWeight.BOLD, color=WHITE),
                            ft.Text("eSports Hub", size=10, color=PINK, weight=ft.FontWeight.W_600),
                        ])
                    ]),
                    ft.Row(spacing=6, controls=[
                        ft.IconButton(icon=ft.Icons.NOTIFICATIONS_OUTLINED, icon_color=MUTED,
                                      tooltip="Notificaciones",
                                      on_click=lambda e: snack("Sin notificaciones pendientes")),
                        ft.Stack(controls=[
                            ft.CircleAvatar(
                                foreground_image_src="https://api.dicebear.com/7.x/bottts/png?seed=LotusGamer",
                                radius=17),
                            ft.Container(width=10, height=10, bgcolor=GREEN, border_radius=5,
                                         border=ft.Border.all(2, CARD), right=0, bottom=0)
                        ])
                    ])
                ]
            )
        )

        sub = S["sub"]
        if   sub == "create":     body = view_create_event()
        elif sub == "register":   body = view_register_event()
        elif sub == "agenda":     body = view_agenda()
        elif sub == "chat_open":  body = view_chat_open()
        elif sub == "events_hub": body = view_events_hub()
        else:
            t = min(S["tab"], 4)
            # Tab labels: Inicio, Torneos, Agenda, En Vivo, Chats
            if   t == 0: body = view_dashboard()
            elif t == 1: body = view_events_hub()
            elif t == 2: body = view_agenda()
            elif t == 3: body = view_live()
            elif t == 4: body = view_chats_list()
            else:        body = view_dashboard()

        bnav = ft.NavigationBar(
            selected_index=S["tab"] if sub is None else S["tab"],
            bgcolor=CARD, indicator_color=PINK,
            on_change=lambda e: set_tab(e.control.selected_index),
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.HOME_OUTLINED,          selected_icon=ft.Icons.HOME,          label="Inicio"),
                ft.NavigationBarDestination(icon=ft.Icons.SPORTS_ESPORTS_OUTLINED, selected_icon=ft.Icons.SPORTS_ESPORTS,label="Torneos"),
                ft.NavigationBarDestination(icon=ft.Icons.CALENDAR_MONTH_OUTLINED, selected_icon=ft.Icons.CALENDAR_MONTH,label="Agenda"),
                ft.NavigationBarDestination(icon=ft.Icons.LIVE_TV_OUTLINED,        selected_icon=ft.Icons.LIVE_TV,       label="En Vivo"),
                ft.NavigationBarDestination(icon=ft.Icons.CHAT_BUBBLE_OUTLINE,     selected_icon=ft.Icons.CHAT_BUBBLE,   label="Chats"),
            ]
        )

        return ft.Column(expand=True, spacing=0, controls=[
            header,
            ft.Container(expand=True, content=body),
            bnav
        ])

    render()


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
