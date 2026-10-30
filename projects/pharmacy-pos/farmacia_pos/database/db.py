"""
Configuración y Conexión a Base de Datos - Farmacia POS
Soporta dos entornos:
1. TEST (Prueba / MySQL Workbench local):
   "Driver={SQL };Server=127.0.1.0;Database=farmacia;UID=root;PWD=admin;"
   Crea la base de datos 'farmacia' automáticamente si no existe y genera las tablas.
2. PROD (Producción / Original SQL Server):
   "Driver={SQL Server};Server=192.168.1.10;Database=Nikoly;UID=Nikoly_sa;PWD=NIKOLYbe4;"
"""
import os
import sys
import urllib.parse
from datetime import date, datetime, timedelta
from decimal import Decimal
import random

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

from .models import Base, Sucursal, Rol, Usuario, Producto, Lote, Venta, DetalleVenta

# Variable global para el estado del entorno actual
DB_ENV = os.getenv("FARMACIA_ENV", "test").lower()

# Configuraciones de conexión
CONFIGS = {
    "test": {
        "name": "Prueba (MySQL Workbench Local)",
        "driver": "{SQL }",
        "server": "127.0.1.0",
        "host": "127.0.0.1",
        "port": 3306,
        "database": "farmacia",
        "uid": "root",
        "pwd": "admin",
        "raw_conn_str": "Driver={SQL };Server=127.0.1.0;Database=farmacia;UID=root;PWD=admin;"
    },
    "prod": {
        "name": "Producción (SQL Server Original)",
        "driver": "{SQL Server}",
        "server": "192.168.1.10",
        "database": "Nikoly",
        "uid": "Nikoly_sa",
        "pwd": "NIKOLYbe4",
        "raw_conn_str": "Driver={SQL Server};Server=192.168.1.10;Database=Nikoly;UID=Nikoly_sa;PWD=NIKOLYbe4;"
    }
}

_engine = None
_session_factory = None
_active_env_info = {}


def create_mysql_database_if_not_exists(host: str, port: int, user: str, password: str, db_name: str) -> bool:
    """
    Crea la base de datos en MySQL si aún no existe.
    Usa pymysql o mysql.connector.
    """
    try:
        import pymysql
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            connect_timeout=5
        )
        with conn.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
        conn.commit()
        conn.close()
        print(f"[DB INFO] Base de datos '{db_name}' verificada/creada exitosamente en MySQL.")
        return True
    except Exception as e:
        print(f"[DB WARNING] Intento con pymysql: {e}")
        try:
            import mysql.connector
            conn = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                connection_timeout=5
            )
            cursor = conn.cursor()
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
            conn.commit()
            cursor.close()
            conn.close()
            print(f"[DB INFO] Base de datos '{db_name}' verificada/creada con mysql.connector.")
            return True
        except Exception as e2:
            print(f"[DB ERROR] No se pudo crear/verificar DB en MySQL: {e2}")
            return False


def get_engine(env: str = None):
    """
    Obtiene o inicializa el motor SQLAlchemy según el entorno.
    """
    global _engine, DB_ENV, _active_env_info, _session_factory
    target_env = (env or DB_ENV or "test").lower()

    if _engine is not None and target_env == _active_env_info.get("env"):
        return _engine

    _session_factory = None
    cfg = CONFIGS.get(target_env, CONFIGS["test"])
    _active_env_info = {"env": target_env, "name": cfg["name"]}

    if target_env == "test":
        host = "127.0.0.1"
        port = cfg.get("port", 3306)
        user = cfg["uid"]
        pwd = cfg["pwd"]
        db = cfg["database"]

        create_mysql_database_if_not_exists(host, port, user, pwd, db)

        try:
            safe_pwd = urllib.parse.quote_plus(pwd)
            url = f"mysql+pymysql://{user}:{safe_pwd}@{host}:{port}/{db}?charset=utf8mb4"
            _engine = create_engine(url, pool_pre_ping=True, pool_recycle=3600)
            with _engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"[DB OK] Conectado exitosamente a MySQL: {host}/{db}")
        except Exception as err:
            print(f"[DB WARNING] Fallo conexión PyMySQL: {err}. Probando ODBC...")
            try:
                params = urllib.parse.quote_plus(
                    f"Driver={{MySQL ODBC 8.0 Unicode Driver}};Server={cfg['server']};"
                    f"Database={db};UID={user};PWD={pwd};"
                )
                _engine = create_engine(f"mysql+pyodbc:///?odbc_connect={params}", pool_pre_ping=True)
                with _engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
            except Exception as err_odbc:
                print(f"[DB WARNING] Falló ODBC: {err_odbc}. Activando SQLite fallback...")
                sqlite_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "farmacia_test.db"))
                _engine = create_engine(f"sqlite:///{sqlite_path}", echo=False)
                _active_env_info["fallback_sqlite"] = True
                print(f"[DB INFO] Modo SQLite local activado: {sqlite_path}")

    elif target_env == "prod":
        server = cfg["server"]
        db = cfg["database"]
        uid = cfg["uid"]
        pwd = cfg["pwd"]

        try:
            odbc_str = (
                f"Driver={{SQL Server}};"
                f"Server={server};"
                f"Database={db};"
                f"UID={uid};"
                f"PWD={pwd};"
            )
            params = urllib.parse.quote_plus(odbc_str)
            _engine = create_engine(
                f"mssql+pyodbc:///?odbc_connect={params}",
                pool_pre_ping=True,
                pool_recycle=1800
            )
            with _engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"[DB OK] Conectado a SQL Server Producción: {server}/{db}")
        except Exception as err:
            print(f"[DB ERROR] Error al conectar a SQL Server en {server}: {err}")
            sqlite_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "farmacia_prod_cache.db"))
            _engine = create_engine(f"sqlite:///{sqlite_path}", echo=False)
            _active_env_info["fallback_sqlite"] = True
            _active_env_info["error_remote"] = str(err)

    return _engine


def get_session():
    """
    Retorna una sesión de SQLAlchemy vinculada al engine activo.
    """
    global _session_factory
    engine = get_engine()
    if _session_factory is None:
        _session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return _session_factory()


def check_and_apply_migrations(engine):
    """
    Verifica que las tablas tengan las columnas requeridas (por ejemplo, id_sucursal).
    Aplica alteraciones DDL automáticamente si faltan.
    """
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        # Si lotes existe pero no tiene id_sucursal, agregarla
        if "lotes" in tables:
            cols = [c["name"] for c in inspector.get_columns("lotes")]
            if "id_sucursal" not in cols:
                print("[MIGRATION] Agregando columna 'id_sucursal' a tabla 'lotes'...")
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE lotes ADD COLUMN id_sucursal INT NOT NULL DEFAULT 1"))

        # Si ventas existe pero no tiene id_sucursal, agregarla
        if "ventas" in tables:
            cols = [c["name"] for c in inspector.get_columns("ventas")]
            if "id_sucursal" not in cols:
                print("[MIGRATION] Agregando columna 'id_sucursal' a tabla 'ventas'...")
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE ventas ADD COLUMN id_sucursal INT NOT NULL DEFAULT 1"))

    except Exception as e:
        print(f"[MIGRATION WARNING] Verificación de columnas: {e}")


def init_db(env: str = None):
    """
    Crea las tablas en la base de datos si no existen y precarga datos iniciales (sucursales, roles, usuarios, productos).
    """
    engine = get_engine(env)

    # 1. Crear todas las tablas definidas en models.py
    print("[DB INIT] Verificando y creando tablas del sistema...")
    Base.metadata.create_all(bind=engine)

    # 2. Verificar columnas adicionales en tablas preexistentes
    check_and_apply_migrations(engine)
    print("[DB INIT] Tablas verificadas exitosamente.")

    # 3. Poblar datos iniciales y semillas (Seed Data)
    seed_initial_data()


def seed_initial_data():
    """
    Inserta sucursales iniciales, roles, usuarios por defecto y productos con lotes
    distribuidos por sucursal, además de ventas históricas para gráficos y KPIs.
    """
    from ..services.auth_service import hash_password

    session = get_session()
    try:
        # A. Sucursales
        suc_count = session.query(Sucursal).count()
        if suc_count == 0:
            suc1 = Sucursal(
                nombre="Farmacia Central",
                direccion="Av. Salud y Esperanza #450, Centro",
                telefono="(555) 789-2345",
                activo=True
            )
            suc2 = Sucursal(
                nombre="Sucursal Norte",
                direccion="Blvd. Las Palmas #120, Col. Norte",
                telefono="(555) 321-7654",
                activo=True
            )
            suc3 = Sucursal(
                nombre="Sucursal Plaza Sur",
                direccion="Av. Comercial Sur #88, Plaza Médica",
                telefono="(555) 987-6543",
                activo=True
            )
            session.add_all([suc1, suc2, suc3])
            session.commit()
            print("[DB SEED] Sucursales 'Central', 'Norte' y 'Plaza Sur' creadas.")

        # B. Roles
        roles_exist = session.query(Rol).count()
        if roles_exist == 0:
            rol_admin = Rol(nombre="admin", descripcion="Administrador del sistema con acceso total")
            rol_empleado = Rol(nombre="empleado", descripcion="Empleado / Cajero con acceso al Punto de Venta")
            session.add_all([rol_admin, rol_empleado])
            session.commit()
            print("[DB SEED] Roles 'admin' y 'empleado' creados.")

        # C. Usuarios por defecto (con contraseña encriptada)
        admin_rol = session.query(Rol).filter_by(nombre="admin").first()
        empleado_rol = session.query(Rol).filter_by(nombre="empleado").first()

        user_count = session.query(Usuario).count()
        if user_count == 0 and admin_rol and empleado_rol:
            admin_user = Usuario(
                username="admin",
                password_hash=hash_password("admin123"),
                nombre_completo="Lic. Administrador General",
                id_rol=admin_rol.id,
                activo=True
            )
            cajero_user = Usuario(
                username="cajero",
                password_hash=hash_password("cajero123"),
                nombre_completo="Dra. Ana López (Farmacéutica)",
                id_rol=empleado_rol.id,
                activo=True
            )
            session.add_all([admin_user, cajero_user])
            session.commit()
            print("[DB SEED] Usuarios iniciales creados con contraseñas encriptadas.")

        # D. Productos y Lotes distribuidos por Sucursales (Diferentes stocks por sucursal)
        prod_count = session.query(Producto).count()
        today = date.today()

        sucursales = session.query(Sucursal).all()
        id_central = sucursales[0].id if sucursales else 1
        id_norte = sucursales[1].id if len(sucursales) > 1 else id_central
        id_sur = sucursales[2].id if len(sucursales) > 2 else id_central

        if prod_count == 0:
            # Producto 1
            prod1 = Producto(
                codigo_barras="750100010001",
                nombre="Paracetamol 500mg (Caja 20 Tabletas)",
                descripcion="Analgésico y antipirético de uso común",
                principio_activo="Paracetamol",
                laboratorio="Genéricos Farma",
                precio_venta=Decimal("35.50"),
                precio_costo=Decimal("15.00"),
                requiere_receta=False,
                activo=True
            )
            # Producto 2
            prod2 = Producto(
                codigo_barras="750100020002",
                nombre="Amoxicilina 500mg (Caja 12 Cápsulas)",
                descripcion="Antibiótico bactericida de amplio espectro",
                principio_activo="Amoxicilina",
                laboratorio="BioLab Farmacéutica",
                precio_venta=Decimal("89.00"),
                precio_costo=Decimal("45.00"),
                requiere_receta=True,
                activo=True
            )
            # Producto 3
            prod3 = Producto(
                codigo_barras="750100030003",
                nombre="Ibuprofeno 400mg (Caja 10 Tabletas)",
                descripcion="Antiinflamatorio no esteroideo (AINE)",
                principio_activo="Ibuprofeno",
                laboratorio="Serral Laboratories",
                precio_venta=Decimal("42.00"),
                precio_costo=Decimal("18.50"),
                requiere_receta=False,
                activo=True
            )
            # Producto 4
            prod4 = Producto(
                codigo_barras="750100040004",
                nombre="Omeprazol 20mg (Caja 14 Cápsulas)",
                descripcion="Inhibidor de la bomba de protones",
                principio_activo="Omeprazol",
                laboratorio="Medix",
                precio_venta=Decimal("55.00"),
                precio_costo=Decimal("22.00"),
                requiere_receta=False,
                activo=True
            )
            # Producto 5
            prod5 = Producto(
                codigo_barras="750100050005",
                nombre="Electrolitos Orales Fresa 500ml",
                descripcion="Solución rehidratante oral",
                principio_activo="Glucosa y Electrolitos",
                laboratorio="SaludVida",
                precio_venta=Decimal("28.00"),
                precio_costo=Decimal("12.00"),
                requiere_receta=False,
                activo=True
            )
            session.add_all([prod1, prod2, prod3, prod4, prod5])
            session.flush()

        # Lotes distribuidos por Sucursal (Stocks independientes)
        lotes_norte_count = session.query(Lote).filter_by(id_sucursal=id_norte).count()
        if lotes_norte_count == 0:
            products_list = session.query(Producto).all()
            if len(products_list) >= 5:
                p1, p2, p3, p4, p5 = products_list[0], products_list[1], products_list[2], products_list[3], products_list[4]

                # SUCURSAL NORTE (Diferente stock)
                l1_n1 = Lote(id_producto=p1.id, id_sucursal=id_norte, numero_lote="LOT-PAR-N1", fecha_vencimiento=today + timedelta(days=180), stock_actual=50, costo_compra=Decimal("15.00"))
                l3_n1 = Lote(id_producto=p3.id, id_sucursal=id_norte, numero_lote="LOT-IBU-N1", fecha_vencimiento=today + timedelta(days=210), stock_actual=40, costo_compra=Decimal("18.50"))
                l5_n1 = Lote(id_producto=p5.id, id_sucursal=id_norte, numero_lote="LOT-ELE-N1", fecha_vencimiento=today + timedelta(days=280), stock_actual=60, costo_compra=Decimal("12.00"))

                # SUCURSAL PLAZA SUR (Diferente stock)
                l2_s1 = Lote(id_producto=p2.id, id_sucursal=id_sur, numero_lote="LOT-AMX-S1", fecha_vencimiento=today + timedelta(days=120), stock_actual=18, costo_compra=Decimal("45.00"))
                l3_s1 = Lote(id_producto=p3.id, id_sucursal=id_sur, numero_lote="LOT-IBU-S1", fecha_vencimiento=today + timedelta(days=95), stock_actual=25, costo_compra=Decimal("18.50"))
                l4_s1 = Lote(id_producto=p4.id, id_sucursal=id_sur, numero_lote="LOT-OMP-S1", fecha_vencimiento=today + timedelta(days=320), stock_actual=35, costo_compra=Decimal("22.00"))

                session.add_all([l1_n1, l3_n1, l5_n1, l2_s1, l3_s1, l4_s1])
                session.commit()
                print("[DB SEED] Lotes independientes agregados a Sucursal Norte y Plaza Sur.")

        # E. Ventas históricas para alimentar KPIs y Gráficos interactivos
        sales_count = session.query(Venta).count()
        if sales_count < 10:
            print("[DB SEED] Generando ventas históricas para gráficos y KPIs...")
            user = session.query(Usuario).first()
            user_id = user.id if user else 1
            products = session.query(Producto).all()
            metodos = ["Efectivo", "Tarjeta de Débito", "Tarjeta de Crédito", "Transferencia"]
            metodo_weights = [0.50, 0.25, 0.15, 0.10]
            suc_list = [id_central, id_norte, id_sur]

            # Generar ventas para los últimos 14 días
            now = datetime.now()
            folio_num = 100
            for days_ago in range(13, -1, -1):
                sale_date = now - timedelta(days=days_ago, hours=random.randint(1, 8), minutes=random.randint(0, 50))
                # 2 a 5 ventas por día
                for _ in range(random.randint(2, 5)):
                    folio_num += 1
                    suc_chosen = random.choice(suc_list)
                    metodo_chosen = random.choices(metodos, weights=metodo_weights)[0]

                    # Seleccionar 1 o 2 productos
                    sample_prods = random.sample(products, k=min(2, len(products)))
                    subtotal = Decimal("0.00")
                    items_det = []

                    for pr in sample_prods:
                        cant = random.randint(1, 3)
                        sub_it = (pr.precio_venta * cant).quantize(Decimal("0.01"))
                        subtotal += sub_it
                        items_det.append((pr.id, cant, pr.precio_venta, sub_it))

                    iva = (subtotal * Decimal("0.16")).quantize(Decimal("0.01"))
                    total = subtotal + iva

                    v = Venta(
                        folio=f"TCK-{sale_date.strftime('%Y%m%d')}-{folio_num:03d}",
                        id_usuario=user_id,
                        id_sucursal=suc_chosen,
                        fecha=sale_date,
                        subtotal=subtotal,
                        impuesto=iva,
                        total=total,
                        metodo_pago=metodo_chosen,
                        monto_recibido=total,
                        cambio=Decimal("0.00"),
                        cliente=random.choice(["Público General", "María González", "Carlos Rivera", "Laura Méndez", "Roberto Silva"])
                    )
                    session.add(v)
                    session.flush()

                    for pid, cant, pv, sub_it in items_det:
                        det = DetalleVenta(
                            id_venta=v.id,
                            id_producto=pid,
                            id_lote=None,
                            cantidad=cant,
                            precio_unitario=pv,
                            subtotal=sub_it
                        )
                        session.add(det)

            session.commit()
            print("[DB SEED] Historial de ventas multi-sucursal cargado para visualizaciones.")

    except Exception as e:
        session.rollback()
        print(f"[DB SEED ERROR] Error en seed_initial_data: {e}")
    finally:
        session.close()


def get_active_connection_info() -> dict:
    """Retorna información detallada sobre la conexión activa para mostrar en la interfaz."""
    cfg = CONFIGS.get(DB_ENV, CONFIGS["test"])
    info = {
        "env": DB_ENV,
        "name": cfg["name"],
        "server": cfg["server"],
        "database": cfg["database"],
        "raw_string": cfg["raw_conn_str"],
        "is_fallback": _active_env_info.get("fallback_sqlite", False),
        "engine_url": str(_engine.url) if _engine else "No inicializado"
    }
    return info
