"""
Simulación y Formato de Impresión de Tickets de Farmacia
Genera tickets térmicos profesionales con trazabilidad de lotes (FEFO) y previsualizador.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from typing import Dict, Any


def generate_ticket_text(sale_data: Dict[str, Any], pharmacy_name: str = "FARMASHIELD") -> str:
    """
    Genera el formato en texto plano tipo ticket térmico (40-42 columnas).
    Incluye trazabilidad de Lote y Fecha de Vencimiento de cada producto vendido.
    """
    w = 42
    lines = []
    lines.append("=" * w)
    suc_name = sale_data.get("sucursal_nombre", pharmacy_name)
    suc_dir = sale_data.get("sucursal_direccion", "Av. Salud y Esperanza #450, Centro")
    suc_tel = sale_data.get("sucursal_telefono", "Tel: (555) 789-2345")

    lines.append(f"{suc_name.center(w)}")
    lines.append("CUIDANDO TU SALUD Y BIENESTAR".center(w))
    lines.append("RFC: FSH-20261014-K09".center(w))
    if len(suc_dir) > w:
        suc_dir = suc_dir[:w-2]
    lines.append(f"{suc_dir.center(w)}")
    lines.append(f"{suc_tel.center(w)}")
    lines.append("=" * w)

    lines.append(f"FOLIO:    {sale_data.get('folio', 'N/A')}")
    lines.append(f"SUCURSAL: {suc_name}")
    lines.append(f"FECHA:    {sale_data.get('fecha', datetime.now().strftime('%d/%m/%Y %H:%M'))}")
    lines.append(f"CAJERO:   {sale_data.get('cajero', 'Personal de Caja')}")
    lines.append(f"CLIENTE:  {sale_data.get('cliente', 'Público General')}")
    lines.append("-" * w)
    lines.append(f"{'CANT':<4} {'DESCRIPCIÓN':<23} {'TOTAL':>13}")
    lines.append("-" * w)

    for item in sale_data.get("articulos", []):
        nombre = item["nombre"]
        if len(nombre) > 23:
            nombre = nombre[:21] + ".."
        total_item = f"${item['subtotal']:.2f}"
        lines.append(f"{item['cantidad']:<4} {nombre:<23} {total_item:>13}")

        # Trazabilidad de Lote y Caducidad (Sistema FEFO)
        lote_str = f"  -> Lote: {item.get('lote', 'N/A')} (Vence: {item.get('fecha_vence', 'N/A')})"
        lines.append(lote_str)

    lines.append("-" * w)
    subtotal = sale_data.get("subtotal", 0.0)
    iva = sale_data.get("iva", 0.0)
    total = sale_data.get("total", 0.0)
    pago = sale_data.get("monto_recibido", total)
    cambio = sale_data.get("cambio", 0.0)
    metodo = sale_data.get("metodo_pago", "Efectivo")

    lines.append(f"{'SUBTOTAL:':<25} ${subtotal:>14.2f}")
    lines.append(f"{'I.V.A. (16%):':<25} ${iva:>14.2f}")
    lines.append(f"{'TOTAL A PAGAR:':<25} ${total:>14.2f}")
    lines.append("-" * w)
    lines.append(f"{'MÉTODO DE PAGO:':<25} {metodo:>15}")
    lines.append(f"{'IMPORTE RECIBIDO:':<25} ${pago:>14.2f}")
    lines.append(f"{'CAMBIO ENTREGADO:':<25} ${cambio:>14.2f}")
    lines.append("=" * w)
    lines.append("* MEDICAMENTOS CERTIFICADOS POR FEFO *".center(w))
    lines.append("CONSERVE SU TICKET PARA CUALQUIER ACLARACIÓN".center(w))
    lines.append("NO SE ACEPTAN DEVOLUCIONES DE MEDICAMENTOS".center(w))
    lines.append("¡GRACIAS POR SU PREFERENCIA!".center(w))
    lines.append("=" * w)

    return "\n".join(lines)


def save_ticket_to_file(sale_data: Dict[str, Any], target_dir: str = None) -> str:
    """Guarda el ticket en un archivo de texto en el directorio 'tickets'."""
    if not target_dir:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        target_dir = os.path.join(base_dir, "tickets")

    os.makedirs(target_dir, exist_ok=True)
    folio = sale_data.get("folio", f"TICKET_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    filename = f"{folio.replace(':', '_').replace('/', '_')}.txt"
    filepath = os.path.join(target_dir, filename)

    ticket_content = generate_ticket_text(sale_data)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(ticket_content)

    return filepath


def show_ticket_modal(parent: tk.Tk or tk.Toplevel, sale_data: Dict[str, Any]):
    """
    Despliega una ventana modal interactiva con el ticket formateado en diseño térmico.
    Permite guardarlo en disco o simular la impresión directa.
    """
    from ..ui.styles import (
        COLOR_BG, COLOR_PANEL, COLOR_PRIMARY, COLOR_PRIMARY_HOVER,
        COLOR_PRIMARY_ACTIVE, COLOR_TEXT_WHITE, COLOR_TEXT,
        FONT_TITLE, FONT_BOLD, FONT_MONO
    )

    ticket_text = generate_ticket_text(sale_data)

    modal = tk.Toplevel(parent)
    modal.title(f"Ticket de Venta - {sale_data.get('folio', '')}")
    modal.geometry("450x640")
    modal.configure(bg=COLOR_BG)
    modal.transient(parent)
    modal.grab_set()

    # Centrar la ventana en la pantalla
    modal.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() // 2) - 225
    y = parent.winfo_y() + (parent.winfo_height() // 2) - 320
    modal.geometry(f"+{max(0, x)}+{max(0, y)}")

    # Cabecera Verde FarmaShield
    header_frame = tk.Frame(modal, bg=COLOR_PRIMARY, padx=16, pady=12)
    header_frame.pack(fill="x")

    lbl_title = tk.Label(
        header_frame,
        text="🧾 Comprobante de Venta",
        bg=COLOR_PRIMARY,
        fg=COLOR_TEXT_WHITE,
        font=FONT_TITLE
    )
    lbl_title.pack(anchor="w")

    lbl_sub = tk.Label(
        header_frame,
        text=f"Folio: {sale_data.get('folio', '')} | {sale_data.get('fecha', '')}",
        bg=COLOR_PRIMARY,
        fg=COLOR_BG,
        font=("Segoe UI", 9)
    )
    lbl_sub.pack(anchor="w")

    # Contenedor del Ticket Térmico
    content_frame = tk.Frame(modal, bg=COLOR_BG, padx=16, pady=10)
    content_frame.pack(fill="both", expand=True)

    text_box = tk.Text(
        content_frame,
        bg=COLOR_PANEL,
        fg=COLOR_TEXT,
        font=FONT_MONO,
        wrap="none",
        relief="solid",
        borderwidth=1,
        padx=10,
        pady=10
    )
    scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=text_box.yview)
    text_box.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    text_box.pack(side="left", fill="both", expand=True)

    text_box.insert("1.0", ticket_text)
    text_box.configure(state="disabled")

    # Barra inferior con botones de acción
    btn_frame = tk.Frame(modal, bg=COLOR_BG, padx=16, pady=12)
    btn_frame.pack(fill="x")

    def on_save_file():
        saved_path = save_ticket_to_file(sale_data)
        messagebox.showinfo(
            "Ticket Guardado",
            f"El ticket fue guardado exitosamente en:\n{saved_path}",
            parent=modal
        )

    def on_print_simulation():
        saved_path = save_ticket_to_file(sale_data)
        messagebox.showinfo(
            "Impresión Exitosa",
            f"Simulación de impresión enviada a impresora térmica de 80mm/58mm.\nCopia respaldada en:\n{saved_path}",
            parent=modal
        )
        modal.destroy()

    btn_print = ttk.Button(
        btn_frame,
        text="🖨️ Imprimir Ticket",
        style="Pink.TButton",
        command=on_print_simulation
    )
    btn_print.pack(side="left", padx=5)

    btn_save = ttk.Button(
        btn_frame,
        text="💾 Guardar .txt",
        style="Secondary.TButton",
        command=on_save_file
    )
    btn_save.pack(side="left", padx=5)

    btn_close = ttk.Button(
        btn_frame,
        text="Cerrar",
        style="Secondary.TButton",
        command=modal.destroy
    )
    btn_close.pack(side="right", padx=5)
