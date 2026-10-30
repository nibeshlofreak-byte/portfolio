"""
Servicio de Autenticación y Control de Acceso Basado en Roles (RBAC)
Pilar 1: Seguridad en Credenciales con hashing bcrypt y control de roles.
"""
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy.orm import joinedload
from ..database.db import get_session
from ..database.models import Usuario, Rol, Sucursal

# Usuario y Sucursal en sesión activa en memoria
_current_session_user: Optional[Usuario] = None
_current_session_branch: Optional[Sucursal] = None


def hash_password(plain_password: str) -> str:
    """
    Genera un hash seguro con sal para la contraseña usando bcrypt.
    Tiene fallback a werkzeug.security si bcrypt no estuviera disponible.
    """
    if not plain_password:
        raise ValueError("La contraseña no puede estar vacía.")

    try:
        import bcrypt
        salt = bcrypt.gensalt(rounds=12)
        pwd_bytes = plain_password.encode("utf-8")
        hashed = bcrypt.hashpw(pwd_bytes, salt)
        return hashed.decode("utf-8")
    except Exception:
        # Fallback de respaldo con werkzeug
        from werkzeug.security import generate_password_hash
        return generate_password_hash(plain_password, method="scrypt")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si una contraseña en texto plano coincide con el hash almacenado.
    Soporta formato bcrypt y werkzeug.
    """
    if not plain_password or not hashed_password:
        return False

    try:
        if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"):
            import bcrypt
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8")
            )
        else:
            from werkzeug.security import check_password_hash
            return check_password_hash(hashed_password, plain_password)
    except Exception as e:
        print(f"[AUTH ERROR] Error al verificar contraseña: {e}")
        return False


def login(username: str, plain_password: str, sucursal_id: Optional[int] = None) -> Tuple[bool, Optional[Usuario], str]:
    """
    Autentica un usuario verificando credenciales, estado activo y sucursal elegida.
    Retorna (éxito, usuario, mensaje).
    """
    global _current_session_user, _current_session_branch

    username_clean = (username or "").strip()
    if not username_clean or not plain_password:
        return False, None, "Debe ingresar usuario y contraseña."

    session = get_session()
    try:
        user = (
            session.query(Usuario)
            .options(joinedload(Usuario.rol))
            .filter(Usuario.username == username_clean)
            .first()
        )

        if not user:
            return False, None, "Usuario no encontrado."

        if not user.activo:
            return False, None, "La cuenta de usuario está desactivada. Contacte al administrador."

        if not verify_password(plain_password, user.password_hash):
            return False, None, "Contraseña incorrecta."

        # Establecer sucursal de trabajo
        if sucursal_id is not None:
            suc = session.query(Sucursal).get(sucursal_id)
        else:
            suc = session.query(Sucursal).filter_by(activo=True).first()

        _current_session_user = user
        _current_session_branch = suc

        suc_nombre = suc.nombre if suc else "Sucursal General"
        return True, user, f"Bienvenido/a {user.nombre_completo} | Sucursal: {suc_nombre}"

    except Exception as e:
        return False, None, f"Error durante el inicio de sesión: {e}"
    finally:
        session.close()


def logout() -> None:
    """Cierra la sesión actual del sistema y libera la sucursal activa."""
    global _current_session_user, _current_session_branch
    _current_session_user = None
    _current_session_branch = None


def get_current_user() -> Optional[Usuario]:
    """Retorna el usuario que ha iniciado sesión actualmente."""
    return _current_session_user


def get_current_branch() -> Optional[Sucursal]:
    """Retorna la sucursal seleccionada para la sesión actual."""
    return _current_session_branch


def get_current_branch_id() -> int:
    """Retorna el ID de la sucursal actual o 1 por defecto."""
    if _current_session_branch:
        return _current_session_branch.id
    return 1


def set_current_branch(sucursal_id: int) -> bool:
    """Cambia la sucursal activa en la sesión."""
    global _current_session_branch
    session = get_session()
    try:
        suc = session.query(Sucursal).get(sucursal_id)
        if suc and suc.activo:
            _current_session_branch = suc
            return True
        return False
    finally:
        session.close()


def is_authenticated() -> bool:
    """Verifica si hay una sesión activa."""
    return _current_session_user is not None


def has_role(required_role: str) -> bool:
    """
    Verifica si el usuario actual posee un rol específico (ej. 'admin' o 'empleado').
    """
    if not _current_session_user or not _current_session_user.rol:
        return False
    return _current_session_user.rol.nombre.lower() == required_role.lower()


def is_admin() -> bool:
    """Atajo para comprobar si el usuario actual es administrador."""
    return has_role("admin")


def create_user(
    username: str,
    plain_password: str,
    nombre_completo: str,
    rol_nombre: str
) -> Tuple[bool, str]:
    """
    Crea un nuevo usuario en la base de datos con contraseña encriptada (bcrypt).
    """
    username_clean = (username or "").strip().lower()
    nombre_clean = (nombre_completo or "").strip()

    if not username_clean or len(username_clean) < 3:
        return False, "El nombre de usuario debe tener al menos 3 caracteres."

    if not plain_password or len(plain_password) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres."

    if not nombre_clean:
        return False, "El nombre completo es requerido."

    session = get_session()
    try:
        # Verificar duplicado
        existing = session.query(Usuario).filter_by(username=username_clean).first()
        if existing:
            return False, f"El nombre de usuario '{username_clean}' ya está en uso."

        rol = session.query(Rol).filter_by(nombre=rol_nombre.lower()).first()
        if not rol:
            return False, f"El rol '{rol_nombre}' no existe."

        hashed = hash_password(plain_password)
        new_user = Usuario(
            username=username_clean,
            password_hash=hashed,
            nombre_completo=nombre_clean,
            id_rol=rol.id,
            activo=True
        )
        session.add(new_user)
        session.commit()
        return True, f"Usuario '{username_clean}' creado exitosamente."

    except Exception as e:
        session.rollback()
        return False, f"Error al registrar usuario: {e}"
    finally:
        session.close()


def list_users() -> List[Dict[str, Any]]:
    """Obtiene el listado de usuarios con sus roles y estados."""
    session = get_session()
    try:
        users = session.query(Usuario).options(joinedload(Usuario.rol)).order_by(Usuario.id.asc()).all()
        result = []
        for u in users:
            result.append({
                "id": u.id,
                "username": u.username,
                "nombre_completo": u.nombre_completo,
                "rol": u.rol.nombre if u.rol else "Sin Rol",
                "activo": u.activo,
                "created_at": u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else ""
            })
        return result
    finally:
        session.close()


def toggle_user_status(user_id: int) -> Tuple[bool, str]:
    """Activa o desactiva un usuario."""
    session = get_session()
    try:
        user = session.query(Usuario).get(user_id)
        if not user:
            return False, "Usuario no encontrado."

        if user.username == "admin" and user.activo:
            return False, "No se puede desactivar la cuenta principal de administrador."

        user.activo = not user.activo
        session.commit()
        estado = "activado" if user.activo else "desactivado"
        return True, f"Usuario '{user.username}' {estado} correctamente."
    except Exception as e:
        session.rollback()
        return False, f"Error al actualizar estado: {e}"
    finally:
        session.close()


def list_roles() -> List[str]:
    """Retorna los nombres de roles disponibles en el sistema."""
    session = get_session()
    try:
        roles = session.query(Rol).all()
        return [r.nombre for r in roles]
    finally:
        session.close()
