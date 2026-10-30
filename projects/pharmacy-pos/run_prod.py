"""
Script Ejecutable ORIGINAL / PRODUCCIÓN (SQL Server)
====================================================
Conexión de producción:
  Driver={SQL Server};
  Server=192.168.1.10;
  Database=Nikoly;
  UID=Nikoly_sa;
  PWD=NIKOLYbe4;

Verifica y genera las tablas en 'Nikoly' si no existen.
"""
import os
import sys

# Establecer entorno de producción antes de importar los módulos
os.environ["FARMACIA_ENV"] = "prod"

# Asegurar path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from farmacia_pos.main import MainApplication


def run():
    print("=" * 65)
    print("  INICIANDO FARMASHIELD - MODO ORIGINAL / PRODUCCIÓN (SQL SERVER)")
    print("  Conexión: 192.168.1.10 / Base de datos: Nikoly / Usuario: Nikoly_sa")
    print("=" * 65)
    app = MainApplication(target_env="prod")
    app.mainloop()


if __name__ == "__main__":
    run()
