# ⚕️ Farmacia POS - Sistema de Punto de Venta, Multi-Sucursal & Analítica FEFO

Sistema integral de punto de venta (POS) y administración farmacéutica desarrollado en Python, diseñado con una elegante **identidad visual en tonos rosas**, alta seguridad criptográfica en credenciales, motor estricto de **descuento de inventario por caducidad (FEFO: First Expired, First Out)**, **gestión multi-sucursal con stocks independientes** y un módulo avanzado de **KPIs y Gráficos Interactivos**.

---

## 📂 Estructura del Proyecto

```text
farmacia_pos/
│
├── database/                # Persistencia de datos y conexión multientorno
│   ├── __init__.py
│   ├── db.py                # Conexiones (MySQL Workbench / SQL Server / SQLite) + Migraciones
│   └── models.py            # Tablas: Sucursales, Roles, Usuarios, Productos, Lotes, Ventas, DetalleVenta
│
├── services/                # Reglas de negocio y analítica
│   ├── __init__.py
│   ├── auth_service.py      # Autenticación con bcrypt, control RBAC y sucursal en sesión
│   ├── inventory_service.py # Control de stock multi-sucursal y algoritmo FEFO
│   ├── sales_service.py     # Carrito, cálculo de subtotales/IVA y transacciones
│   └── analytics_service.py # Cálculo de KPIs, tendencias temporales y distribución gráfica
│
├── ui/                      # Interfaz gráfica moderna en tonos rosas
│   ├── __init__.py
│   ├── styles.py            # Paleta de colores rosada (#C75B7A, #FDFBFB, etc.) y temas TTK
│   ├── login_view.py        # Pantalla de acceso con selector de sucursal de operación
│   ├── admin_view.py        # Panel de Administrador (KPIs, gráficos Matplotlib, sucursales, reportes)
│   └── pos_view.py          # Pantalla de Ventas para Empleado/Caja con stock por sucursal
│
├── utils/                   # Soporte e impresión
│   ├── __init__.py
│   └── printer.py           # Formato de ticket térmico con membrete de sucursal y trazabilidad FEFO
│
├── main.py                  # Orquestador del ciclo de vida y enrutamiento RBAC
├── requirements.txt         # Dependencias del proyecto
└── README.md                # Documentación completa
```

---

## 📊 Módulo de KPIs y Gráficos Interactivos (`admin_view.py` y `analytics_service.py`)

### 1. Indicadores Clave de Rendimiento (KPIs en Tiempo Real)
- **💵 Ventas del Día:** Suma acumulada de ingresos generados hoy.
- **📅 Ventas del Mes:** Ingresos acumulados durante el mes en curso.
- **🎟️ Ticket Promedio:** Monto medio de compra por transacción ($\text{Ingresos} / \text{Transacciones}$).
- **💰 Total de Ingresos Filtrados:** Recaudación en el período y sucursal elegida.
- **🛒 Cantidad de Transacciones:** Número de ventas efectuadas y unidades de producto dispensadas.

### 2. Cuatro Gráficos Interactivos Integrados (Matplotlib en Tonos Rosas)
1. **Curva de Tendencia Temporal:** Evolución de ventas diarias en los últimos 14 días con línea rosa estilizada (`#C75B7A`) y relleno degradado suave (`#F8E7F0`).
2. **Top Medicamentos Más Vendidos:** Gráfico de barras horizontales con los medicamentos líderes en unidades desplazadas.
3. **Distribución por Métodos de Pago:** Gráfico circular / donut con porcentajes de ventas por Efectivo, Tarjeta de Débito, Crédito y Transferencia.
4. **Comparativa entre Sucursales:** Gráfico de barras que compara el rendimiento financiero entre cada una de las sucursales activas.

### 3. Filtros Dinámicos
- **Por Sucursal:** *Todas las Sucursales*, *Farmacia Central*, *Sucursal Norte*, *Sucursal Plaza Sur*, o cualquier sucursal nueva creada.
- **Por Fecha / Período:** *Hoy*, *Últimos 7 Días*, *Últimos 30 Días*, *Este Mes*, *Historial Completo*.

---

## 🏢 Gestión Multi-Sucursal & Stocks Independientes

- **Diferentes Stocks por Sucursal:** Cada sucursal mantiene sus propios lotes y existencias. Si la *Sucursal Central* tiene 50 unidades de Paracetamol y la *Sucursal Norte* tiene 20, cada una descuenta de su stock local.
- **Selección de Sucursal al Ingreso:** Al iniciar sesión en `login_view.py`, el empleado o cajero selecciona en qué sucursal va a operar.
- **Control en Caja (POS):** La pantalla de ventas muestra en el encabezado la sucursal activa, filtra las búsquedas y deducciones al stock de esa sucursal, y emite tickets con los datos fiscales de dicha sucursal.
- **Alta de Nuevas Sucursales:** Desde el panel de administración se pueden registrar nuevas sucursales (Nombre, Dirección, Teléfono).

---

## 💡 Los 4 Pilares Fundamentales

1. **Seguridad en Credenciales (`auth_service.py`):** Contraseñas encriptadas con `bcrypt` y sal aleatoria.
2. **Control de Acceso Basado en Roles - RBAC (`main.py`):** Redirección automática a la vista administrativa o a la caja restringida.
3. **Identidad Visual Rosada (`ui/styles.py`):** Paleta `#C75B7A`, `#921A40`, `#FDFBFB`, `#E0A9B8`, `#F8E7F0`.
4. **Validación de Lotes FEFO (`inventory_service.py`):** Descuento automático del lote más próximo a vencer en la sucursal activa y semáforo de caducidades.

---

## 🚀 Entornos de Ejecución

### Modo Prueba (MySQL Workbench Local)
```bash
python run_test.py
```
Cadena: `Driver={SQL };Server=127.0.1.0;Database=farmacia;UID=root;PWD=admin;`
*(Auto-crea la base de datos `farmacia`, tablas, sucursales y datos de prueba).*

### Modo Producción / Original (SQL Server Remoto)
```bash
python run_prod.py
```
Cadena: `Driver={SQL Server};Server=192.168.1.10;Database=Nikoly;UID=Nikoly_sa;PWD=NIKOLYbe4;`
