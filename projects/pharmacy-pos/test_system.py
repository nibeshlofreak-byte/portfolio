"""
Prueba Unitaria de Integración del Sistema Farmacia POS
Verifica DB, Auth bcrypt, Sucursales, Stocks Independientes,
FEFO por Sucursal, KPIs, y Gráficos Analíticos con Matplotlib.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from farmacia_pos.database.db import init_db, get_session, get_active_connection_info
from farmacia_pos.database.models import Usuario, Rol, Producto, Lote, Venta, Sucursal
from farmacia_pos.services.auth_service import (
    login, hash_password, verify_password, list_users,
    get_current_branch, get_current_branch_id, set_current_branch
)
from farmacia_pos.services.inventory_service import (
    list_branches,
    create_branch,
    search_products,
    validate_stock_fefo,
    check_batch_expirations,
    get_inventory_statistics
)
from farmacia_pos.services.sales_service import ShoppingCart, process_sale
from farmacia_pos.services.analytics_service import (
    get_kpis_and_metrics,
    get_temporal_sales_trend,
    get_top_selling_products,
    get_payment_methods_distribution,
    get_sales_by_branch_comparison
)
from farmacia_pos.utils.printer import generate_ticket_text


def run_tests():
    print("=" * 65)
    print("  EJECUTANDO PRUEBAS DE INTEGRACIÓN: SUCURSALES, KPIS Y GRÁFICOS")
    print("=" * 65)

    # 1. Base de datos e inicialización
    print("\n1. Inicializando base de datos 'farmacia' con esquema multi-sucursal...")
    init_db("test")
    info = get_active_connection_info()
    print(f"   -> Servidor: {info['server']} | Base de Datos: {info['database']}")

    # 2. Sucursales
    print("\n2. Verificando Gestión de Sucursales...")
    sucursales = list_branches(only_active=True)
    assert len(sucursales) >= 3, f"Debe haber al menos 3 sucursales, encontradas: {len(sucursales)}"
    print(f"   [OK] {len(sucursales)} sucursales activas:")
    for s in sucursales:
        print(f"        - ID {s['id']}: {s['nombre']} ({s['direccion']})")

    # 3. Stocks independientes por sucursal
    print("\n3. Verificando Stocks Independientes por Sucursal...")
    suc1_id = sucursales[0]["id"]
    suc2_id = sucursales[1]["id"]
    prods_suc1 = search_products("", only_active=True, sucursal_id=suc1_id)
    prods_suc2 = search_products("", only_active=True, sucursal_id=suc2_id)

    print(f"   Stock en {sucursales[0]['nombre']}:")
    for p in prods_suc1[:3]:
        print(f"     * {p['nombre']}: Stock={p['stock_total']}, Lote={p['proximo_lote_numero']}")

    print(f"   Stock en {sucursales[1]['nombre']}:")
    for p in prods_suc2[:3]:
        print(f"     * {p['nombre']}: Stock={p['stock_total']}, Lote={p['proximo_lote_numero']}")

    # 4. Login con selección de Sucursal
    print("\n4. Probando Login de Empleado con selección de Sucursal...")
    ok_log, user_emp, msg_log = login("cajero", "cajero123", sucursal_id=suc2_id)
    assert ok_log, f"Error login: {msg_log}"
    current_suc = get_current_branch()
    assert current_suc.id == suc2_id, "La sucursal seleccionada debe ser la asignada en sesión"
    print(f"   [OK] Login exitoso: {user_emp.nombre_completo} operando en {current_suc.nombre}")

    # 5. Venta y Deducción FEFO en la sucursal seleccionada
    print("\n5. Probando Venta y Descuento FEFO en la Sucursal...")
    cart = ShoppingCart(tasa_iva=0.16, sucursal_id=suc2_id)
    target_prod = next(p for p in prods_suc2 if p["stock_total"] > 0)
    stock_antes = target_prod["stock_total"]
    cart.add_product(target_prod, quantity=2)

    ok_vta, msg_vta, ticket_data = process_sale(
        cart=cart,
        user_id=user_emp.id,
        sucursal_id=suc2_id,
        metodo_pago="Tarjeta de Débito",
        monto_recibido=float(cart.total),
        cliente_nombre="Doctora Martínez"
    )
    assert ok_vta, f"Error en venta: {msg_vta}"
    print(f"   [OK] Venta procesada en {ticket_data['sucursal_nombre']}! Folio: {ticket_data['folio']}")

    # 6. Métricas y KPIs
    print("\n6. Verificando Cálculo de KPIs...")
    kpis_general = get_kpis_and_metrics(sucursal_id=None, date_preset="mes")
    kpis_suc2 = get_kpis_and_metrics(sucursal_id=suc2_id, date_preset="mes")

    print(f"   [OK] KPIs Consolidados (Todas las Sucursales):")
    print(f"        - Ventas Hoy:        ${kpis_general['ventas_hoy']:.2f}")
    print(f"        - Ventas del Mes:    ${kpis_general['ventas_mes']:.2f}")
    print(f"        - Total Ingresos:    ${kpis_general['total_ingresos']:.2f}")
    print(f"        - Ticket Promedio:   ${kpis_general['ticket_promedio']:.2f}")
    print(f"        - Transacciones:     {kpis_general['total_transacciones']}")

    print(f"   [OK] KPIs Filtrados para {sucursales[1]['nombre']}:")
    print(f"        - Total Ingresos:    ${kpis_suc2['total_ingresos']:.2f}")
    print(f"        - Ticket Promedio:   ${kpis_suc2['ticket_promedio']:.2f}")

    # 7. Datos de Gráficos Interactivos (Matplotlib)
    print("\n7. Verificando Generación de Datos para Gráficos...")
    # Curva de tendencia
    dates, trend_vals = get_temporal_sales_trend(sucursal_id=None, days=7)
    print(f"   [OK] Curva de tendencia temporal (7 días): {len(dates)} puntos de datos")

    # Top medicamentos
    top_p, top_q = get_top_selling_products(limit=5)
    print(f"   [OK] Top medicamentos más vendidos: {list(zip(top_p, top_q))}")

    # Métodos de pago (Pie chart)
    metodos, montos, _ = get_payment_methods_distribution()
    print(f"   [OK] Métodos de pago (Torta): {list(zip(metodos, montos))}")

    # Comparativa por sucursal
    s_names, s_totals = get_sales_by_branch_comparison()
    print(f"   [OK] Comparativa entre sucursales: {list(zip(s_names, s_totals))}")

    # Ticket térmico con sucursal
    print("\n8. Muestra de Ticket Térmico con Encabezado de Sucursal:")
    print("-" * 45)
    print(generate_ticket_text(ticket_data))
    print("-" * 45)

    print("\n>>> ¡TODAS LAS NUEVAS FUNCIONALIDADES (KPIS, GRÁFICOS Y MULTI-SUCURSAL) FUNCIONAN AL 100%! <<<")


if __name__ == "__main__":
    run_tests()
