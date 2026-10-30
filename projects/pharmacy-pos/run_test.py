"""
Script Ejecutable de PRUEBA (MySQL Workbench Local)
===================================================
Conexión de prueba:
  Driver={SQL };
  Server=127.0.1.0;
  Database=farmacia;
  UID=root;
  PWD=admin;

Si la base de datos 'farmacia' o sus tablas no existen, las crea automáticamente.
"""
import os
import sys

# Establecer entorno de prueba antes de importar los módulos
os.environ["FARMACIA_ENV"] = "test"

# Asegurar path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from farmacia_pos.main import MainApplication


def run():
    print("=" * 65)
    print("  INICIANDO FARMASHIELD - MODO PRUEBA (WORKBENCH / MYSQL)")
    print("  Conexión: 127.0.1.0 / Base de datos: farmacia / Usuario: root")
    print("=" * 65)
    app = MainApplication(target_env="test")
    app.mainloop()


if __name__ == "__main__":
    run()
