"""
Acceso Directo Principal - Farmacia POS
Permite arrancar la aplicación pasando argumentos por consola:
  python main.py --env test    (Prueba MySQL Workbench)
  python main.py --env prod    (Producción SQL Server Nikoly)
O por defecto arranca en modo prueba (test).
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from farmacia_pos.main import main

if __name__ == "__main__":
    main()
