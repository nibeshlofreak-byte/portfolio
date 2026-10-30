"""
Modelos de Datos SQLAlchemy para Farmacia POS
Define las tablas: Sucursales, Roles, Usuarios, Productos, Lotes, Ventas y DetalleVenta.
"""
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Boolean,
    DateTime,
    Date,
    ForeignKey,
    Text
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Sucursal(Base):
    """
    Tabla de Sucursales de la Farmacia.
    Permite gestionar inventarios independientes y aislar ventas por sucursal.
    """
    __tablename__ = "sucursales"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), unique=True, nullable=False, index=True)
    direccion = Column(String(200), nullable=True)
    telefono = Column(String(50), nullable=True)
    activo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    lotes = relationship("Lote", back_populates="sucursal", cascade="all, delete-orphan")
    ventas = relationship("Venta", back_populates="sucursal")

    def __repr__(self):
        return f"<Sucursal id={self.id} nombre='{self.nombre}'>"


class Rol(Base):
    """
    Tabla de Roles del sistema (RBAC):
    Ej: 'admin', 'empleado' (o cajero)
    """
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), unique=True, nullable=False, index=True)
    descripcion = Column(String(200), nullable=True)

    usuarios = relationship("Usuario", back_populates="rol", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Rol id={self.id} nombre='{self.nombre}'>"


class Usuario(Base):
    """
    Tabla de Usuarios del sistema con contraseñas encriptadas (bcrypt).
    """
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nombre_completo = Column(String(120), nullable=False)
    id_rol = Column(Integer, ForeignKey("roles.id"), nullable=False)
    activo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    rol = relationship("Rol", back_populates="usuarios")
    ventas = relationship("Venta", back_populates="usuario")

    def __repr__(self):
        return f"<Usuario id={self.id} username='{self.username}' rol='{self.rol.nombre if self.rol else None}'>"


class Producto(Base):
    """
    Tabla de Productos / Medicamentos en catálogo general.
    """
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo_barras = Column(String(50), unique=True, nullable=False, index=True)
    nombre = Column(String(150), nullable=False, index=True)
    descripcion = Column(String(255), nullable=True)
    principio_activo = Column(String(150), nullable=True)
    laboratorio = Column(String(100), nullable=True)
    precio_venta = Column(Numeric(10, 2), nullable=False)
    precio_costo = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    requiere_receta = Column(Boolean, default=False, nullable=False)
    activo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    lotes = relationship("Lote", back_populates="producto", cascade="all, delete-orphan")
    detalles = relationship("DetalleVenta", back_populates="producto")

    def get_stock_total(self, id_sucursal: int = None) -> int:
        """Calcula el stock total sumando los lotes activos no vencidos (opcionalmente filtrado por sucursal)."""
        today = date.today()
        batches = [
            l for l in self.lotes
            if l.stock_actual > 0 and l.fecha_vencimiento >= today
        ]
        if id_sucursal is not None:
            batches = [l for l in batches if l.id_sucursal == id_sucursal]
        return sum(l.stock_actual for l in batches)

    @property
    def stock_total(self) -> int:
        return self.get_stock_total()

    def __repr__(self):
        return f"<Producto id={self.id} codigo='{self.codigo_barras}' nombre='{self.nombre}'>"


class Lote(Base):
    """
    Tabla de Lotes para control estricto de caducidad (FEFO) y stock asignado por sucursal.
    """
    __tablename__ = "lotes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_producto = Column(Integer, ForeignKey("productos.id"), nullable=False, index=True)
    id_sucursal = Column(Integer, ForeignKey("sucursales.id"), nullable=False, default=1, index=True)
    numero_lote = Column(String(50), nullable=False, index=True)
    fecha_vencimiento = Column(Date, nullable=False, index=True)
    stock_actual = Column(Integer, nullable=False, default=0)
    costo_compra = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    producto = relationship("Producto", back_populates="lotes")
    sucursal = relationship("Sucursal", back_populates="lotes")
    detalles = relationship("DetalleVenta", back_populates="lote")

    @property
    def dias_para_vencer(self) -> int:
        """Días restantes antes de la fecha de caducidad."""
        today = date.today()
        return (self.fecha_vencimiento - today).days

    @property
    def esta_vencido(self) -> bool:
        return self.dias_para_vencer < 0

    def __repr__(self):
        return (
            f"<Lote id={self.id} lote='{self.numero_lote}' sucursal={self.id_sucursal} "
            f"vence={self.fecha_vencimiento} stock={self.stock_actual}>"
        )


class Venta(Base):
    """
    Tabla de Ventas / Transacciones de Caja con registro de sucursal.
    """
    __tablename__ = "ventas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    folio = Column(String(50), unique=True, nullable=False, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    id_sucursal = Column(Integer, ForeignKey("sucursales.id"), nullable=False, default=1, index=True)
    fecha = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    subtotal = Column(Numeric(10, 2), nullable=False)
    impuesto = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    metodo_pago = Column(String(50), default="Efectivo", nullable=False)
    monto_recibido = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    cambio = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    cliente = Column(String(100), default="Público General", nullable=False)

    usuario = relationship("Usuario", back_populates="ventas")
    sucursal = relationship("Sucursal", back_populates="ventas")
    detalles = relationship("DetalleVenta", back_populates="venta", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Venta id={self.id} folio='{self.folio}' sucursal={self.id_sucursal} total={self.total}>"


class DetalleVenta(Base):
    """
    Detalle de productos vendidos. Registra el lote específico de donde
    se descontó el inventario bajo el criterio FEFO en la sucursal correspondiente.
    """
    __tablename__ = "detalle_venta"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_venta = Column(Integer, ForeignKey("ventas.id"), nullable=False, index=True)
    id_producto = Column(Integer, ForeignKey("productos.id"), nullable=False, index=True)
    id_lote = Column(Integer, ForeignKey("lotes.id"), nullable=True, index=True)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)

    venta = relationship("Venta", back_populates="detalles")
    producto = relationship("Producto", back_populates="detalles")
    lote = relationship("Lote", back_populates="detalles")

    def __repr__(self):
        return (
            f"<DetalleVenta id={self.id} venta={self.id_venta} "
            f"producto={self.id_producto} cant={self.cantidad} subtotal={self.subtotal}>"
        )
