"""
Servicio de Ventas y Transacciones de Caja - Farmacia POS
Lógica del carrito de compras, cálculo de totales, integración con FEFO y sucursales.
"""
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional, Tuple

from sqlalchemy.orm import joinedload
from ..database.db import get_session
from ..database.models import Venta, DetalleVenta, Usuario, Producto, Lote, Sucursal
from .inventory_service import deduct_stock_fefo, validate_stock_fefo


@dataclass
class CartItem:
    """Representa un producto dentro del carrito de ventas."""
    producto_id: int
    codigo_barras: str
    nombre: str
    precio_unitario: Decimal
    cantidad: int
    requiere_receta: bool = False
    proximo_lote: str = ""
    vencimiento_proximo: str = ""
    alerta_vencimiento: Optional[str] = None

    @property
    def subtotal(self) -> Decimal:
        return (self.precio_unitario * self.cantidad).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class ShoppingCart:
    """Gestor del carrito de compras en memoria para el punto de venta ligado a una sucursal."""

    def __init__(self, tasa_iva: float = 0.16, sucursal_id: int = 1):
        self.items: Dict[int, CartItem] = {}
        self.tasa_iva = Decimal(str(tasa_iva))
        self.sucursal_id = sucursal_id

    def set_sucursal(self, sucursal_id: int):
        """Si cambia de sucursal, vacía el carrito para evitar inconsistencias de inventario."""
        if self.sucursal_id != sucursal_id:
            self.sucursal_id = sucursal_id
            self.clear()

    def add_product(self, product_dict: dict, quantity: int = 1) -> Tuple[bool, str]:
        """Agrega un producto al carrito verificando stock FEFO disponible en la sucursal activa."""
        pid = product_dict["id"]
        current_in_cart = self.items[pid].cantidad if pid in self.items else 0
        total_wanted = current_in_cart + quantity

        is_ok, available, msg = validate_stock_fefo(pid, total_wanted, sucursal_id=self.sucursal_id)
        if not is_ok:
            return False, msg

        if pid in self.items:
            self.items[pid].cantidad = total_wanted
        else:
            self.items[pid] = CartItem(
                producto_id=pid,
                codigo_barras=product_dict.get("codigo_barras", ""),
                nombre=product_dict.get("nombre", ""),
                precio_unitario=Decimal(str(product_dict.get("precio_venta", 0.0))),
                cantidad=quantity,
                requiere_receta=product_dict.get("requiere_receta", False),
                proximo_lote=product_dict.get("proximo_lote_numero", "N/A"),
                vencimiento_proximo=product_dict.get("proximo_lote_vence", "N/A"),
                alerta_vencimiento=product_dict.get("alerta_vencimiento")
            )

        return True, f"'{product_dict['nombre']}' agregado al carrito."

    def update_quantity(self, product_id: int, new_quantity: int) -> Tuple[bool, str]:
        """Modifica la cantidad de un producto en el carrito."""
        if product_id not in self.items:
            return False, "El producto no está en el carrito."

        if new_quantity <= 0:
            return self.remove_product(product_id)

        is_ok, available, msg = validate_stock_fefo(product_id, new_quantity, sucursal_id=self.sucursal_id)
        if not is_ok:
            return False, msg

        self.items[product_id].cantidad = new_quantity
        return True, "Cantidad actualizada."

    def remove_product(self, product_id: int) -> Tuple[bool, str]:
        """Elimina un producto del carrito."""
        if product_id in self.items:
            item = self.items.pop(product_id)
            return True, f"'{item.nombre}' eliminado del carrito."
        return False, "El producto no se encontraba en el carrito."

    def clear(self):
        """Vacía el carrito."""
        self.items.clear()

    @property
    def subtotal(self) -> Decimal:
        total = sum((item.subtotal for item in self.items.values()), Decimal("0.00"))
        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def impuesto(self) -> Decimal:
        iva = self.subtotal * self.tasa_iva
        return iva.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def total(self) -> Decimal:
        return (self.subtotal + self.impuesto).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def total_articulos(self) -> int:
        return sum(item.cantidad for item in self.items.values())

    def get_items_list(self) -> List[Dict[str, Any]]:
        result = []
        for item in self.items.values():
            result.append({
                "id": item.producto_id,
                "codigo": item.codigo_barras,
                "nombre": item.nombre,
                "precio": float(item.precio_unitario),
                "cantidad": item.cantidad,
                "subtotal": float(item.subtotal),
                "lote": item.proximo_lote,
                "vence": item.vencimiento_proximo,
                "alerta": item.alerta_vencimiento,
                "receta": item.requiere_receta
            })
        return result


def process_sale(
    cart: ShoppingCart,
    user_id: int,
    sucursal_id: int = 1,
    metodo_pago: str = "Efectivo",
    monto_recibido: float = 0.0,
    cliente_nombre: str = "Público General"
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Registra la venta transaccionalmente vinculada a una sucursal:
    1. Descuenta stock aplicando FEFO en los lotes de esa sucursal.
    2. Crea el registro en 'ventas' con id_sucursal.
    3. Crea los registros en 'detalle_venta' con el id_lote exacto deducido.
    4. Retorna el resumen listo para imprimir el ticket.
    """
    if not cart.items:
        return False, "El carrito de compras está vacío.", None

    subtotal_dec = cart.subtotal
    iva_dec = cart.impuesto
    total_dec = cart.total
    monto_rec_dec = Decimal(str(monto_recibido)) if monto_recibido > 0 else total_dec

    if metodo_pago == "Efectivo" and monto_rec_dec < total_dec:
        return False, f"El monto recibido (${monto_rec_dec}) es menor al total a pagar (${total_dec}).", None

    cambio_dec = (monto_rec_dec - total_dec).quantize(Decimal("0.01")) if metodo_pago == "Efectivo" else Decimal("0.00")

    session = get_session()
    try:
        now = datetime.now()
        prefix = f"TCK-{now.strftime('%Y%m%d%H%M')}"
        last_sale = session.query(Venta).filter(Venta.folio.like(f"{prefix}%")).order_by(Venta.id.desc()).first()
        secuencia = 1
        if last_sale and "-" in last_sale.folio:
            try:
                secuencia = int(last_sale.folio.split("-")[-1]) + 1
            except Exception:
                secuencia = 1
        folio = f"{prefix}-{secuencia:03d}"

        # 1. Crear cabecera de Venta con sucursal
        nueva_venta = Venta(
            folio=folio,
            id_usuario=user_id,
            id_sucursal=sucursal_id,
            fecha=now,
            subtotal=subtotal_dec,
            impuesto=iva_dec,
            total=total_dec,
            metodo_pago=metodo_pago,
            monto_recibido=monto_rec_dec,
            cambio=cambio_dec,
            cliente=(cliente_nombre or "Público General").strip()
        )
        session.add(nueva_venta)
        session.flush()

        detalles_ticket = []

        # 2. Descontar stock por FEFO en la sucursal seleccionada
        for item in cart.items.values():
            deducciones = deduct_stock_fefo(session, item.producto_id, item.cantidad, sucursal_id=sucursal_id)

            for ded in deducciones:
                sub_parcial = (item.precio_unitario * ded["cantidad_descontada"]).quantize(Decimal("0.01"))
                det = DetalleVenta(
                    id_venta=nueva_venta.id,
                    id_producto=item.producto_id,
                    id_lote=ded["id_lote"],
                    cantidad=ded["cantidad_descontada"],
                    precio_unitario=item.precio_unitario,
                    subtotal=sub_parcial
                )
                session.add(det)

                detalles_ticket.append({
                    "nombre": item.nombre,
                    "cantidad": ded["cantidad_descontada"],
                    "precio_unitario": float(item.precio_unitario),
                    "subtotal": float(sub_parcial),
                    "lote": ded["numero_lote"],
                    "fecha_vence": ded["fecha_vencimiento"].strftime("%d/%m/%Y")
                })

        session.commit()

        cajero_user = session.query(Usuario).get(user_id)
        cajero_nombre = cajero_user.nombre_completo if cajero_user else "Cajero"

        suc = session.query(Sucursal).get(sucursal_id)
        suc_nombre = suc.nombre if suc else "Farmacia Central"
        suc_dir = suc.direccion if suc else "Av. Salud y Esperanza #450, Centro"
        suc_tel = suc.telefono if suc else "(555) 789-2345"

        ticket_data = {
            "folio": folio,
            "id_venta": nueva_venta.id,
            "sucursal_nombre": suc_nombre,
            "sucursal_direccion": suc_dir,
            "sucursal_telefono": suc_tel,
            "fecha": now.strftime("%d/%m/%Y %H:%M:%S"),
            "cajero": cajero_nombre,
            "cliente": nueva_venta.cliente,
            "metodo_pago": metodo_pago,
            "articulos": detalles_ticket,
            "subtotal": float(subtotal_dec),
            "iva": float(iva_dec),
            "total": float(total_dec),
            "monto_recibido": float(monto_rec_dec),
            "cambio": float(cambio_dec)
        }

        cart.clear()
        return True, f"Venta registrada con Folio: {folio} en {suc_nombre}", ticket_data

    except Exception as e:
        session.rollback()
        return False, f"Error al procesar la venta: {e}", None
    finally:
        session.close()


def get_sales_history(limit: int = 50, sucursal_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Obtiene el historial reciente de ventas con filtro por sucursal."""
    session = get_session()
    try:
        q = (
            session.query(Venta)
            .options(joinedload(Venta.usuario), joinedload(Venta.sucursal), joinedload(Venta.detalles))
        )
        if sucursal_id is not None:
            q = q.filter(Venta.id_sucursal == sucursal_id)

        ventas = q.order_by(Venta.fecha.desc()).limit(limit).all()
        result = []
        for v in ventas:
            result.append({
                "id": v.id,
                "folio": v.folio,
                "fecha": v.fecha.strftime("%d/%m/%Y %H:%M"),
                "cajero": v.usuario.nombre_completo if v.usuario else "Desconocido",
                "sucursal": v.sucursal.nombre if v.sucursal else f"Sucursal #{v.id_sucursal}",
                "cliente": v.cliente,
                "total": float(v.total),
                "metodo_pago": v.metodo_pago,
                "total_articulos": sum(d.cantidad for d in v.detalles)
            })
        return result
    finally:
        session.close()


def get_sale_details(sale_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene el detalle completo de una venta específica incluyendo los lotes y sucursal."""
    session = get_session()
    try:
        v = (
            session.query(Venta)
            .options(
                joinedload(Venta.usuario),
                joinedload(Venta.sucursal),
                joinedload(Venta.detalles).joinedload(DetalleVenta.producto),
                joinedload(Venta.detalles).joinedload(DetalleVenta.lote)
            )
            .filter(Venta.id == sale_id)
            .first()
        )
        if not v:
            return None

        items = []
        for d in v.detalles:
            prod_name = d.producto.nombre if d.producto else "Producto"
            lote_num = d.lote.numero_lote if d.lote else "N/A"
            vence = d.lote.fecha_vencimiento.strftime("%d/%m/%Y") if d.lote else "N/A"
            items.append({
                "nombre": prod_name,
                "lote": lote_num,
                "vence": vence,
                "cantidad": d.cantidad,
                "precio_unitario": float(d.precio_unitario),
                "subtotal": float(d.subtotal)
            })

        return {
            "id": v.id,
            "folio": v.folio,
            "sucursal_nombre": v.sucursal.nombre if v.sucursal else "Farmacia Central",
            "sucursal_direccion": v.sucursal.direccion if v.sucursal else "",
            "sucursal_telefono": v.sucursal.telefono if v.sucursal else "",
            "fecha": v.fecha.strftime("%d/%m/%Y %H:%M:%S"),
            "cajero": v.usuario.nombre_completo if v.usuario else "N/A",
            "cliente": v.cliente,
            "metodo_pago": v.metodo_pago,
            "subtotal": float(v.subtotal),
            "iva": float(v.impuesto),
            "total": float(v.total),
            "monto_recibido": float(v.monto_recibido),
            "cambio": float(v.cambio),
            "articulos": items
        }
    finally:
        session.close()


def get_sales_summary_today(sucursal_id: Optional[int] = None) -> Dict[str, Any]:
    """Calcula el total de ventas acumulado en el día de hoy (opcionalmente filtrado por sucursal)."""
    session = get_session()
    try:
        today = date.today()
        start_of_day = datetime.combine(today, datetime.min.time())
        q = session.query(Venta).filter(Venta.fecha >= start_of_day)
        if sucursal_id is not None:
            q = q.filter(Venta.id_sucursal == sucursal_id)

        ventas_hoy = q.all()
        total_dinero = sum((v.total for v in ventas_hoy), Decimal("0.00"))
        cantidad_transacciones = len(ventas_hoy)

        return {
            "total_dinero": float(total_dinero),
            "cantidad_transacciones": cantidad_transacciones
        }
    finally:
        session.close()
