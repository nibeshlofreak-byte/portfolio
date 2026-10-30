"""
Servicio de Analítica, KPIs y Métricas - Farmacia POS
Calcula indicadores clave de rendimiento (KPIs), curvas de tendencia temporal,
distribución de métodos de pago y productos más vendidos con filtros por fecha y sucursal.
"""
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy import func, desc
from sqlalchemy.orm import joinedload

from ..database.db import get_session
from ..database.models import Venta, DetalleVenta, Producto, Sucursal, Usuario


def parse_date_filter(date_preset: str = "mes", custom_start: Optional[date] = None, custom_end: Optional[date] = None) -> Tuple[datetime, datetime]:
    """
    Retorna la tupla (start_datetime, end_datetime) según el filtro seleccionado.
    Opciones: 'hoy', '7d', '30d', 'mes', 'todos', 'custom'.
    """
    now = datetime.now()
    today = date.today()

    if date_preset == "hoy":
        start = datetime.combine(today, datetime.min.time())
        end = datetime.combine(today, datetime.max.time())
    elif date_preset == "7d":
        start = datetime.combine(today - timedelta(days=7), datetime.min.time())
        end = datetime.combine(today, datetime.max.time())
    elif date_preset == "30d":
        start = datetime.combine(today - timedelta(days=30), datetime.min.time())
        end = datetime.combine(today, datetime.max.time())
    elif date_preset == "mes":
        start = datetime(today.year, today.month, 1, 0, 0, 0)
        end = datetime.combine(today, datetime.max.time())
    elif date_preset == "custom" and custom_start and custom_end:
        start = datetime.combine(custom_start, datetime.min.time())
        end = datetime.combine(custom_end, datetime.max.time())
    else:  # 'todos'
        start = datetime(2020, 1, 1, 0, 0, 0)
        end = datetime(2099, 12, 31, 23, 59, 59)

    return start, end


def get_kpis_and_metrics(sucursal_id: Optional[int] = None, date_preset: str = "mes") -> Dict[str, Any]:
    """
    Calcula los KPIs requeridos:
    - Ventas del día
    - Ventas del mes
    - Total de ingresos (en el período seleccionado)
    - Ticket promedio ($)
    - Cantidad total de transacciones
    - Total de artículos vendidos
    """
    session = get_session()
    try:
        today = date.today()
        start_today = datetime.combine(today, datetime.min.time())
        start_month = datetime(today.year, today.month, 1, 0, 0, 0)
        start_filtered, end_filtered = parse_date_filter(date_preset)

        # Base queries
        q_today = session.query(func.coalesce(func.sum(Venta.total), 0)).filter(Venta.fecha >= start_today)
        q_month = session.query(func.coalesce(func.sum(Venta.total), 0)).filter(Venta.fecha >= start_month)
        q_filtered = session.query(
            func.coalesce(func.sum(Venta.total), 0),
            func.count(Venta.id)
        ).filter(Venta.fecha >= start_filtered, Venta.fecha <= end_filtered)

        if sucursal_id is not None:
            q_today = q_today.filter(Venta.id_sucursal == sucursal_id)
            q_month = q_month.filter(Venta.id_sucursal == sucursal_id)
            q_filtered = q_filtered.filter(Venta.id_sucursal == sucursal_id)

        ventas_hoy = float(q_today.scalar() or 0.0)
        ventas_mes = float(q_month.scalar() or 0.0)
        total_ingresos, num_transacciones = q_filtered.first()
        total_ingresos = float(total_ingresos or 0.0)
        num_transacciones = int(num_transacciones or 0)

        ticket_promedio = (total_ingresos / num_transacciones) if num_transacciones > 0 else 0.0

        # Artículos vendidos en el período filtrado
        q_articulos = (
            session.query(func.coalesce(func.sum(DetalleVenta.cantidad), 0))
            .join(Venta, DetalleVenta.id_venta == Venta.id)
            .filter(Venta.fecha >= start_filtered, Venta.fecha <= end_filtered)
        )
        if sucursal_id is not None:
            q_articulos = q_articulos.filter(Venta.id_sucursal == sucursal_id)

        total_articulos = int(q_articulos.scalar() or 0)

        return {
            "ventas_hoy": ventas_hoy,
            "ventas_mes": ventas_mes,
            "total_ingresos": total_ingresos,
            "ticket_promedio": ticket_promedio,
            "total_transacciones": num_transacciones,
            "total_articulos": total_articulos,
            "periodo": date_preset
        }
    finally:
        session.close()


def get_temporal_sales_trend(sucursal_id: Optional[int] = None, days: int = 14) -> Tuple[List[str], List[float]]:
    """
    Retorna la curva de tendencia temporal de ventas diarias (últimos 'days' días).
    Retorna (labels_fechas, montos_ventas).
    """
    session = get_session()
    try:
        today = date.today()
        labels = []
        values = []

        for i in range(days - 1, -1, -1):
            day_target = today - timedelta(days=i)
            start_day = datetime.combine(day_target, datetime.min.time())
            end_day = datetime.combine(day_target, datetime.max.time())

            q = session.query(func.coalesce(func.sum(Venta.total), 0)).filter(
                Venta.fecha >= start_day,
                Venta.fecha <= end_day
            )
            if sucursal_id is not None:
                q = q.filter(Venta.id_sucursal == sucursal_id)

            monto = float(q.scalar() or 0.0)
            labels.append(day_target.strftime("%d/%m"))
            values.append(monto)

        return labels, values
    finally:
        session.close()


def get_top_selling_products(sucursal_id: Optional[int] = None, date_preset: str = "mes", limit: int = 6) -> Tuple[List[str], List[int]]:
    """
    Retorna los medicamentos más vendidos (para gráfico de barras).
    Retorna (nombres_productos, cantidades_vendidas).
    """
    session = get_session()
    try:
        start_date, end_date = parse_date_filter(date_preset)

        q = (
            session.query(
                Producto.nombre,
                func.sum(DetalleVenta.cantidad).label("total_cant")
            )
            .join(DetalleVenta, Producto.id == DetalleVenta.id_producto)
            .join(Venta, DetalleVenta.id_venta == Venta.id)
            .filter(Venta.fecha >= start_date, Venta.fecha <= end_date)
        )
        if sucursal_id is not None:
            q = q.filter(Venta.id_sucursal == sucursal_id)

        rows = (
            q.group_by(Producto.nombre)
            .order_by(desc("total_cant"))
            .limit(limit)
            .all()
        )

        names = []
        quantities = []
        for name, cant in rows:
            # Acortar nombre si es muy extenso para que el gráfico luzca limpio
            short_name = name if len(name) <= 20 else name[:18] + ".."
            names.append(short_name)
            quantities.append(int(cant))

        return names, quantities
    finally:
        session.close()


def get_payment_methods_distribution(sucursal_id: Optional[int] = None, date_preset: str = "mes") -> Tuple[List[str], List[float], List[int]]:
    """
    Retorna la distribución de ventas por métodos de pago (para gráfico circular / torta).
    Retorna (nombres_metodos, totales_dinero, cantidades_operaciones).
    """
    session = get_session()
    try:
        start_date, end_date = parse_date_filter(date_preset)

        q = (
            session.query(
                Venta.metodo_pago,
                func.sum(Venta.total).label("monto"),
                func.count(Venta.id).label("conteo")
            )
            .filter(Venta.fecha >= start_date, Venta.fecha <= end_date)
        )
        if sucursal_id is not None:
            q = q.filter(Venta.id_sucursal == sucursal_id)

        rows = q.group_by(Venta.metodo_pago).all()

        metodos = []
        montos = []
        conteos = []

        for met, monto, cnt in rows:
            metodos.append(met or "Otros")
            montos.append(float(monto or 0.0))
            conteos.append(int(cnt or 0))

        return metodos, montos, conteos
    finally:
        session.close()


def get_sales_by_branch_comparison(date_preset: str = "mes") -> Tuple[List[str], List[float]]:
    """
    Retorna el total de ventas acumulado comparando entre las distintas sucursales.
    Retorna (nombres_sucursales, totales_por_sucursal).
    """
    session = get_session()
    try:
        start_date, end_date = parse_date_filter(date_preset)

        rows = (
            session.query(
                Sucursal.nombre,
                func.coalesce(func.sum(Venta.total), 0).label("total_suc")
            )
            .outerjoin(Venta, (Sucursal.id == Venta.id_sucursal) & (Venta.fecha >= start_date) & (Venta.fecha <= end_date))
            .filter(Sucursal.activo == True)
            .group_by(Sucursal.id, Sucursal.nombre)
            .all()
        )

        nombres = [r[0] for r in rows]
        totales = [float(r[1]) for r in rows]
        return nombres, totales
    finally:
        session.close()
