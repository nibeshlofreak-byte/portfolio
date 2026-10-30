"""
Módulo de Utilidades - Farmacia POS
Herramientas de soporte e impresión de tickets.
"""
from .printer import generate_ticket_text, show_ticket_modal, save_ticket_to_file

__all__ = ["generate_ticket_text", "show_ticket_modal", "save_ticket_to_file"]
