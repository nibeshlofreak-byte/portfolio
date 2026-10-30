"""
Servicio de Inventario y Validación de Lotes por FEFO (First Expired, First Out)
Pilar 4: Control de stock, precios, fechas de caducidad, deducción por lote y filtrado por Sucursales.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload

from ..database.db import get_session
from ..database.models import Producto, Lote, Sucursal


def list_branches(only_active: bool = True) -> List[Dict[str, Any]]:
    """Obtiene la lista de sucursales registradas."""
    session = get_session()
    try:
        q = session.query(Sucursal)
        if only_active:
            q = q.filter_by(activo=True)
        sucursales = q.order_by(Sucursal.id.asc()).all()
        return [
            {
                "id": s.id,
                "nombre": s.nombre,
                "direccion": s.direccion or "",
                "telefono": s.telefono or "",
                "activo": s.activo
            }
            for s in sucursales
        ]
    finally:
        session.close()


def create_branch(nombre: str, direccion: str = "", telefono: str = "") -> Tuple[bool, str, Optional[int]]:
    """Registra una nueva sucursal en el sistema."""
    nom = (nombre or "").strip()
    if not nom:
        return False, "El nombre de la sucursal es obligatorio.", None

    session = get_session()
    try:
        exist = session.query(Sucursal).filter_by(nombre=nom).first()
        if exist:
            return False, f"Ya existe una sucursal con el nombre '{nom}'.", None

        nueva = Sucursal(
            nombre=nom,
            direccion=direccion.strip(),
            telefono=telefono.strip(),
            activo=True
        )
        session.add(nueva)
        session.commit()
        return True, f"Sucursal '{nom}' registrada exitosamente.", nueva.id
    except Exception as e:
        session.rollback()
        return False, f"Error al registrar sucursal: {e}", None
    finally:
        session.close()


def search_products(term: str, only_active: bool = True, sucursal_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Busca productos por código de barras, nombre, principio activo o laboratorio.
    Calcula el stock y el próximo lote a vencer (FEFO) filtrando opcionalmente por sucursal.
    """
    session = get_session()
    try:
        query = session.query(Producto).options(joinedload(Producto.lotes))
        if only_active:
            query = query.filter(Producto.activo == True)

        term_clean = (term or "").strip()
        if term_clean:
            like_term = f"%{term_clean}%"
            query = query.filter(
                or_(
                    Producto.codigo_barras.ilike(like_term),
                    Producto.nombre.ilike(like_term),
                    Producto.principio_activo.ilike(like_term),
                    Producto.laboratorio.ilike(like_term)
                )
            )

        products = query.order_by(Producto.nombre.asc()).all()
        today = date.today()
        result = []

        for p in products:
            # Filtrar lotes activos no vencidos (opcionalmente por sucursal)
            valid_batches = [
                l for l in p.lotes
                if l.stock_actual > 0 and l.fecha_vencimiento >= today
            ]
            if sucursal_id is not None:
                valid_batches = [l for l in valid_batches if l.id_sucursal == sucursal_id]

            # Ordenar por FEFO (fecha más próxima primero)
            valid_batches.sort(key=lambda x: x.fecha_vencimiento)

            stock_total = sum(l.stock_actual for l in valid_batches)
            proximo_lote = valid_batches[0] if valid_batches else None

            alerta_vencimiento = None
            dias_restantes = None
            if proximo_lote:
                dias_restantes = proximo_lote.dias_para_vencer
                if dias_restantes <= 30:
                    alerta_vencimiento = f"¡Atención! Vence en {dias_restantes} días ({proximo_lote.fecha_vencimiento})"
                elif dias_restantes <= 60:
                    alerta_vencimiento = f"Próximo a vencer ({dias_restantes} días)"

            result.append({
                "id": p.id,
                "codigo_barras": p.codigo_barras,
                "nombre": p.nombre,
                "descripcion": p.descripcion or "",
                "principio_activo": p.principio_activo or "",
                "laboratorio": p.laboratorio or "",
                "precio_venta": float(p.precio_venta),
                "precio_costo": float(p.precio_costo),
                "requiere_receta": p.requiere_receta,
                "activo": p.activo,
                "stock_total": stock_total,
                "proximo_lote_numero": proximo_lote.numero_lote if proximo_lote else "Sin stock",
                "proximo_lote_vence": proximo_lote.fecha_vencimiento.strftime("%d/%m/%Y") if proximo_lote else "N/A",
                "proximo_lote_dias": dias_restantes,
                "alerta_vencimiento": alerta_vencimiento,
                "cantidad_lotes_activos": len(valid_batches)
            })

        return result
    finally:
        session.close()


def get_product_by_barcode(barcode: str, sucursal_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Busca un producto exacto por código de barras filtrando por sucursal."""
    barcode_clean = (barcode or "").strip()
    if not barcode_clean:
        return None

    results = search_products(barcode_clean, only_active=True, sucursal_id=sucursal_id)
    for p in results:
        if p["codigo_barras"] == barcode_clean:
            return p
    return results[0] if results else None


def get_product_by_id(product_id: int, sucursal_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Obtiene el detalle completo de un producto por su ID."""
    session = get_session()
    try:
        p = session.query(Producto).options(joinedload(Producto.lotes)).filter(Producto.id == product_id).first()
        if not p:
            return None

        today = date.today()
        batches = []
        lotes_query = p.lotes
        if sucursal_id is not None:
            lotes_query = [l for l in lotes_query if l.id_sucursal == sucursal_id]

        for l in sorted(lotes_query, key=lambda x: x.fecha_vencimiento):
            batches.append({
                "id": l.id,
                "numero_lote": l.numero_lote,
                "id_sucursal": l.id_sucursal,
                "fecha_vencimiento": l.fecha_vencimiento.strftime("%d/%m/%Y"),
                "fecha_obj": l.fecha_vencimiento,
                "stock_actual": l.stock_actual,
                "costo_compra": float(l.costo_compra),
                "dias_restantes": l.dias_para_vencer,
                "esta_vencido": l.esta_vencido
            })

        valid_stock = sum(b["stock_actual"] for b in batches if not b["esta_vencido"] and b["stock_actual"] > 0)

        return {
            "id": p.id,
            "codigo_barras": p.codigo_barras,
            "nombre": p.nombre,
            "descripcion": p.descripcion or "",
            "principio_activo": p.principio_activo or "",
            "laboratorio": p.laboratorio or "",
            "precio_venta": float(p.precio_venta),
            "precio_costo": float(p.precio_costo),
            "requiere_receta": p.requiere_receta,
            "activo": p.activo,
            "stock_total": valid_stock,
            "lotes": batches
        }
    finally:
        session.close()


def get_product_fefo_batches(product_id: int, include_expired: bool = False, sucursal_id: Optional[int] = None) -> List[Lote]:
    """Retorna los lotes de un producto ordenados por fecha de vencimiento ascendente."""
    session = get_session()
    try:
        today = date.today()
        q = session.query(Lote).filter(
            Lote.id_producto == product_id,
            Lote.stock_actual > 0
        )
        if sucursal_id is not None:
            q = q.filter(Lote.id_sucursal == sucursal_id)
        if not include_expired:
            q = q.filter(Lote.fecha_vencimiento >= today)

        return q.order_by(Lote.fecha_vencimiento.asc()).all()
    finally:
        session.close()


def validate_stock_fefo(product_id: int, requested_qty: int, sucursal_id: Optional[int] = None) -> Tuple[bool, int, str]:
    """
    Valida si hay suficiente stock disponible de lotes no vencidos en la sucursal indicada.
    Retorna (es_valido, stock_disponible, mensaje).
    """
    if requested_qty <= 0:
        return False, 0, "La cantidad debe ser mayor a 0."

    session = get_session()
    try:
        today = date.today()
        q = session.query(Lote).filter(
            Lote.id_producto == product_id,
            Lote.stock_actual > 0,
            Lote.fecha_vencimiento >= today
        )
        if sucursal_id is not None:
            q = q.filter(Lote.id_sucursal == sucursal_id)

        lotes = q.order_by(Lote.fecha_vencimiento.asc()).all()
        total_available = sum(l.stock_actual for l in lotes)

        if total_available < requested_qty:
            return False, total_available, f"Stock insuficiente en esta sucursal (Disponible: {total_available}, Requerido: {requested_qty})"

        primer_lote = lotes[0]
        msg = f"Stock disponible ({total_available} un.). Lote a descontar (FEFO): {primer_lote.numero_lote}"
        if primer_lote.dias_para_vencer <= 30:
            msg += f" [ALERTA: Vence en {primer_lote.dias_para_vencer} días]"

        return True, total_available, msg
    finally:
        session.close()


def deduct_stock_fefo(session, product_id: int, quantity: int, sucursal_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Aplica el algoritmo FEFO:
    Descuenta 'quantity' unidades de los lotes del producto en la sucursal especificada,
    comenzando por el que tenga la fecha de caducidad más próxima.
    """
    today = date.today()
    q = session.query(Lote).filter(
        Lote.id_producto == product_id,
        Lote.stock_actual > 0,
        Lote.fecha_vencimiento >= today
    )
    if sucursal_id is not None:
        q = q.filter(Lote.id_sucursal == sucursal_id)

    batches = q.order_by(Lote.fecha_vencimiento.asc()).with_for_update().all()
    total_disponible = sum(b.stock_actual for b in batches)

    if total_disponible < quantity:
        raise ValueError(
            f"Stock insuficiente en sucursal {sucursal_id or 'activa'} para producto ID {product_id}. "
            f"Disponible: {total_disponible}, Requerido: {quantity}"
        )

    deductions = []
    remaining_to_deduct = quantity

    for batch in batches:
        if remaining_to_deduct <= 0:
            break

        take_qty = min(batch.stock_actual, remaining_to_deduct)
        batch.stock_actual -= take_qty
        remaining_to_deduct -= take_qty

        deductions.append({
            "id_lote": batch.id,
            "numero_lote": batch.numero_lote,
            "id_sucursal": batch.id_sucursal,
            "fecha_vencimiento": batch.fecha_vencimiento,
            "cantidad_descontada": take_qty,
            "stock_restante_lote": batch.stock_actual
        })

    return deductions


def check_batch_expirations(days_threshold: int = 60, sucursal_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Genera el reporte de alertas de caducidad (Semáforo FEFO) con soporte de filtro por sucursal.
    """
    session = get_session()
    try:
        today = date.today()
        q = session.query(Lote).options(joinedload(Lote.producto), joinedload(Lote.sucursal)).filter(Lote.stock_actual > 0)
        if sucursal_id is not None:
            q = q.filter(Lote.id_sucursal == sucursal_id)

        lotes = q.all()

        vencidos = []
        riesgo_critico = []
        en_prevencion = []
        seguros = []

        for l in lotes:
            prod_name = l.producto.nombre if l.producto else f"Prod #{l.id_producto}"
            codigo = l.producto.codigo_barras if l.producto else "N/A"
            suc_name = l.sucursal.nombre if l.sucursal else f"Sucursal #{l.id_sucursal}"
            dias = l.dias_para_vencer

            data = {
                "id_lote": l.id,
                "id_producto": l.id_producto,
                "codigo": codigo,
                "producto": prod_name,
                "sucursal": suc_name,
                "numero_lote": l.numero_lote,
                "fecha_vencimiento": l.fecha_vencimiento.strftime("%d/%m/%Y"),
                "stock": l.stock_actual,
                "dias_restantes": dias,
                "costo_compra": float(l.costo_compra)
            }

            if dias < 0:
                data["estado"] = "VENCIDO"
                vencidos.append(data)
            elif dias <= 30:
                data["estado"] = "CRÍTICO"
                riesgo_critico.append(data)
            elif dias <= days_threshold:
                data["estado"] = "POR VENCER"
                en_prevencion.append(data)
            else:
                data["estado"] = "SEGURO"
                seguros.append(data)

        vencidos.sort(key=lambda x: x["dias_restantes"])
        riesgo_critico.sort(key=lambda x: x["dias_restantes"])
        en_prevencion.sort(key=lambda x: x["dias_restantes"])

        return {
            "vencidos": vencidos,
            "criticos": riesgo_critico,
            "por_vencer": en_prevencion,
            "seguros": seguros,
            "resumen": {
                "total_vencidos": len(vencidos),
                "total_criticos": len(riesgo_critico),
                "total_por_vencer": len(en_prevencion),
                "total_seguros": len(seguros)
            }
        }
    finally:
        session.close()


def create_product(
    codigo_barras: str,
    nombre: str,
    descripcion: str = "",
    principio_activo: str = "",
    laboratorio: str = "",
    precio_venta: float = 0.0,
    precio_costo: float = 0.0,
    requiere_receta: bool = False
) -> Tuple[bool, str, Optional[int]]:
    """Crea un nuevo medicamento en el catálogo general."""
    session = get_session()
    try:
        codigo = (codigo_barras or "").strip()
        nom = (nombre or "").strip()

        if not codigo or not nom:
            return False, "Código de barras y nombre son campos obligatorios.", None

        existing = session.query(Producto).filter_by(codigo_barras=codigo).first()
        if existing:
            return False, f"Ya existe un producto con el código de barras '{codigo}'.", None

        nuevo = Producto(
            codigo_barras=codigo,
            nombre=nom,
            descripcion=descripcion.strip(),
            principio_activo=principio_activo.strip(),
            laboratorio=laboratorio.strip(),
            precio_venta=Decimal(str(precio_venta)),
            precio_costo=Decimal(str(precio_costo)),
            requiere_receta=requiere_receta,
            activo=True
        )
        session.add(nuevo)
        session.commit()
        return True, f"Producto '{nom}' registrado exitosamente.", nuevo.id
    except Exception as e:
        session.rollback()
        return False, f"Error al crear producto: {e}", None
    finally:
        session.close()


def create_batch(
    id_producto: int,
    numero_lote: str,
    fecha_vencimiento_str: str,
    stock_inicial: int,
    costo_compra: float = 0.0,
    id_sucursal: int = 1
) -> Tuple[bool, str]:
    """
    Registra un nuevo lote de medicamento con fecha de caducidad asignado a una sucursal específica.
    """
    session = get_session()
    try:
        prod = session.query(Producto).get(id_producto)
        if not prod:
            return False, "El producto especificado no existe."

        suc = session.query(Sucursal).get(id_sucursal)
        if not suc:
            return False, "La sucursal seleccionada no existe."

        lote_num = (numero_lote or "").strip().upper()
        if not lote_num:
            return False, "El número de lote es obligatorio."

        if stock_inicial <= 0:
            return False, "El stock inicial del lote debe ser mayor a 0."

        try:
            if "/" in fecha_vencimiento_str:
                parts = fecha_vencimiento_str.split("/")
                if len(parts) == 3:
                    if len(parts[2]) == 4:
                        exp_date = date(int(parts[2]), int(parts[1]), int(parts[0]))
                    else:
                        exp_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
            else:
                exp_date = datetime.strptime(fecha_vencimiento_str.strip(), "%Y-%m-%d").date()
        except Exception:
            return False, "Formato de fecha inválido. Use AAAA-MM-DD o DD/MM/AAAA."

        nuevo_lote = Lote(
            id_producto=id_producto,
            id_sucursal=id_sucursal,
            numero_lote=lote_num,
            fecha_vencimiento=exp_date,
            stock_actual=stock_inicial,
            costo_compra=Decimal(str(costo_compra))
        )
        session.add(nuevo_lote)
        session.commit()
        return True, f"Lote '{lote_num}' ingresado en '{suc.nombre}' con {stock_inicial} unidades (Vence: {exp_date})."

    except Exception as e:
        session.rollback()
        return False, f"Error al registrar lote: {e}"
    finally:
        session.close()


def get_all_products_with_stock(sucursal_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Listado de todos los productos para la tabla de inventario."""
    return search_products("", only_active=False, sucursal_id=sucursal_id)


def get_inventory_statistics(sucursal_id: Optional[int] = None) -> Dict[str, Any]:
    """Estadísticas generales de inventario para el panel de administración."""
    session = get_session()
    try:
        total_prods = session.query(Producto).count()
        today = date.today()

        q_lotes = session.query(Lote).filter(Lote.stock_actual > 0)
        if sucursal_id is not None:
            q_lotes = q_lotes.filter(Lote.id_sucursal == sucursal_id)

        lotes = q_lotes.all()
        total_unidades = sum(l.stock_actual for l in lotes)
        vencidos = sum(1 for l in lotes if l.fecha_vencimiento < today)
        por_vencer = sum(1 for l in lotes if 0 <= (l.fecha_vencimiento - today).days <= 60)

        return {
            "total_productos": total_prods,
            "total_unidades_stock": total_unidades,
            "lotes_vencidos": vencidos,
            "lotes_por_vencer_60d": por_vencer
        }
    finally:
        session.close()
