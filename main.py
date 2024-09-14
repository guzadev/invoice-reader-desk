import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sqlite3
import pdfplumber
import re
from decimal import Decimal, InvalidOperation
import matplotlib.pyplot as plt
from datetime import datetime

# Mapa de traducción de meses en español a inglés
MONTH_TRANSLATION = {
    "ENERO": "January",
    "FEBRERO": "February",
    "MARZO": "March",
    "ABRIL": "April",
    "MAYO": "May",
    "JUNIO": "June",
    "JULIO": "July",
    "AGOSTO": "August",
    "SEPTIEMBRE": "September",
    "OCTUBRE": "October",
    "NOVIEMBRE": "November",
    "DICIEMBRE": "December"
}


# Convertir los valores de los saldo a flotantes
def convert_to_float(value):
    try:
        return float(round(Decimal(value.replace('.', '').replace(',', '.')), 2))
    except InvalidOperation:
        return None


# Abrir factura
def extract_text_from_pdf(pdf_file_path):

    try:
        with pdfplumber.open(pdf_file_path) as pdf:
            # Extraer el texto de cada pagina
            text = ''
            for page_num, page in enumerate(pdf.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n'
                    else:
                        print(f"No text found on page {page_num}")
                except Exception as e:
                    print(f"Error extracting text from page {page_num}: {e}")
            return text if text else "No text extracted."
    except Exception as e:
        print(f'Error processing the file {pdf_file_path}: {e}')
        return None


# Extraer informacion de la factura con expresiones regulares        
def extract_invoice_info(text):
    # Patrones de expresiones regulares
    mes_actual_pattern = r"\b([A-Z]+-[\d]{2})\b"
    saldo_pattern = r"SALDO ACTUAL\s+([\d.,]+)\s+([\d.,]+)"
    cuotas_section_pattern = r"Total de cuotas a vencer\s+(.+)\n(.+)"

    # Buscar el saldo actual en pesos y dolares
    saldo_match = re.search(saldo_pattern, text)
    if saldo_match:
        saldo_actual_pesos = convert_to_float(saldo_match.group(1))
        saldo_actual_dolares = convert_to_float(saldo_match.group(2))
    else:
        saldo_actual_pesos = "No encontrado"
        saldo_actual_dolares = "No encontrado"
    
    # Buscar el mes actual
    mes_actual_match = re.search(mes_actual_pattern, text)
    mes_actual = mes_actual_match.group(1) if mes_actual_match else "No encontrado"

    # Almacenar los saldos en un diccionario
    saldos = {mes_actual: {'pesos': saldo_actual_pesos, 'dolares': saldo_actual_dolares}}
    
    # Buscar la sección de cuotas
    cuotas_match = re.search(cuotas_section_pattern, text)
    if cuotas_match:
        meses_line = cuotas_match.group(1)
        cuotas_line = cuotas_match.group(2)

        # Capturar los meses
        meses_pattern = r"([A-Z]+-[\d]{2})"
        meses = re.findall(meses_pattern, meses_line)

        # Capturar los valores de las cuotas
        cuotas_pattern = r"\$\s*([\d.,]+)"
        cuotas = re.findall(cuotas_pattern, cuotas_line)
        
        # Convertir los valores de las cuotas a float
        monto_cuota = [convert_to_float(cuota) for cuota in cuotas]
        mes_cuota = [mes.capitalize() for mes in meses]
        # Asociar meses y cuotas
        cuotas_a_vencer = dict(zip(mes_cuota, monto_cuota))
        cuotas_factura_actual = {mes_actual: cuotas_a_vencer}
    else:
        cuotas_a_vencer = {}

    return saldos, cuotas_factura_actual 


# Iniciar base de datos con sus tablas
def database():
    conn = sqlite3.connect('invoices.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS saldos (
        mes TEXT PRIMARY KEY,
        saldo_pesos REAL,
        saldo_dolares REAL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cuotas (
        mes_factura TEXT,
        mes_cuota TEXT,
        monto_cuota REAL,
        PRIMARY KEY (mes_factura, mes_cuota)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS procesados (
        archivo TEXT PRIMARY KEY
    )
    ''')

    conn.commit()
    conn.close()


# Ingreso de datos a la base de datos
def insert_data(saldos, cuotas_factura_actual, archivo):
    conn = sqlite3.connect('invoices.db')
    cursor = conn.cursor()

    for mes, saldo in saldos.items():
        if mes != "No encontrado":
            cursor.execute('SELECT mes FROM saldos WHERE mes = ?', (mes,))
            if cursor.fetchone():
                cursor.execute('''
                UPDATE saldos
                SET saldo_pesos = ?, saldo_dolares = ?
                WHERE mes = ?
                ''', (saldo['pesos'], saldo['dolares'], mes))
            else:
                cursor.execute('''
                INSERT INTO saldos (mes, saldo_pesos, saldo_dolares)
                VALUES (?, ?, ?)
                ''', (mes, saldo['pesos'], saldo['dolares']))

    for mes_factura, cuotas in cuotas_factura_actual.items():
        for mes_cuota, monto_cuota in cuotas.items():
            cursor.execute('SELECT mes_factura, mes_cuota FROM cuotas WHERE mes_factura = ? AND mes_cuota = ?', (mes_factura, mes_cuota))
            if cursor.fetchone():
                cursor.execute('''
                UPDATE cuotas
                SET monto_cuota = ?
                WHERE mes_factura = ? AND mes_cuota = ?
                ''', (monto_cuota, mes_factura, mes_cuota))
            else:
                cursor.execute('''
                INSERT INTO cuotas (mes_factura, mes_cuota, monto_cuota)
                VALUES (?, ?, ?)
                ''', (mes_factura, mes_cuota, monto_cuota))

    # Marcar el archivo como procesado
    cursor.execute('INSERT INTO procesados (archivo) VALUES (?)', (archivo,))

    conn.commit()
    conn.close()


# Verificación de los datos cargados
def verify_data():
    conn = sqlite3.connect('invoices.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM saldos')
    print("Saldos:")
    for row in cursor.fetchall():
        print(row)

    cursor.execute('SELECT * FROM cuotas')
    print("Cuotas a Vencer:")
    for row in cursor.fetchall():
        print(row)

# Graficos
def plot_data(save_path=None):
    conn = sqlite3.connect('invoices.db')
    cursor = conn.cursor()

    cursor.execute('SELECT mes, saldo_pesos, saldo_dolares FROM saldos')
    saldos = cursor.fetchall()

    cursor.execute('SELECT mes_factura, mes_cuota, monto_cuota FROM cuotas')
    cuotas = cursor.fetchall()

    conn.close()

    # Traducir y ordenar los datos por mes
    def translate_month(mes):
        mes_spanish, year = mes.split('-')
        mes_english = MONTH_TRANSLATION[mes_spanish.upper()]
        return datetime.strptime(f"{mes_english}-{year}", '%B-%y')

    saldos.sort(key=lambda x: translate_month(x[0]))
    cuotas.sort(key=lambda x: translate_month(x[1]))

    meses = [row[0] for row in saldos]
    saldo_pesos = [row[1] for row in saldos]
    saldo_dolares = [row[2] for row in saldos]

    # Filtrar los meses que tienen saldo en dólares
    meses_dolares = [mes for mes, saldo in zip(meses, saldo_dolares) if saldo != 0]
    saldo_dolares_filtrado = [saldo for saldo in saldo_dolares if saldo != 0]

    # Filtrar las cuotas de la factura más reciente
    if cuotas:
        cuotas.sort(key=lambda x: translate_month(x[0]), reverse=True)
        mes_factura_reciente = cuotas[0][0]
        cuotas_recientes = [monto_cuota for mes_factura, mes_cuota, monto_cuota in cuotas if mes_factura == mes_factura_reciente]
        meses_cuotas_recientes = [mes_cuota for mes_factura, mes_cuota, monto_cuota in cuotas if mes_factura == mes_factura_reciente]
    else:
        mes_factura_reciente = "No encontrado"
        cuotas_recientes = []
        meses_cuotas_recientes = []

    fig, axs = plt.subplots(3, 1, figsize=(10, 12), constrained_layout=True)

    # Gráfico de Saldos en Pesos
    axs[0].plot(meses, saldo_pesos, marker='o', label='Saldo en Pesos')
    axs[0].set_title('Saldos Mensuales en Pesos')
    axs[0].set_xlabel('Mes')
    axs[0].set_ylabel('Saldo en Pesos')
    axs[0].legend()

    for i, txt in enumerate(saldo_pesos):
        vertical_offset = -20 if txt == max(saldo_pesos) else 10  # Ajustar posición para evitar superposición con el máximo valor
        horizontal_offset = 0  # Asegurar que las anotaciones estén centradas horizontalmente
        if i > 0 and saldo_pesos[i] < saldo_pesos[i-1]:
            vertical_offset = 10  # Ajustar posición para valores decrecientes
        axs[0].annotate(f'{txt:.2f}', (meses[i], saldo_pesos[i]), 
                        textcoords="offset points", xytext=(horizontal_offset, vertical_offset), 
                        ha='center', color='white', bbox=dict(facecolor='black', alpha=0.7, edgecolor='none'))

    # Gráfico de Saldos en Dólares (solo si hay datos)
    if meses_dolares:
        axs[1].plot(meses_dolares, saldo_dolares_filtrado, marker='o', label='Saldo en Dólares', color='orange')
        axs[1].set_title('Saldos Mensuales en Dólares')
        axs[1].set_xlabel('Mes')
        axs[1].set_ylabel('Saldo en Dólares')
        axs[1].legend()

        for i, txt in enumerate(saldo_dolares_filtrado):
            vertical_offset = -20 if txt == max(saldo_dolares_filtrado) else 10  # Ajustar posición para evitar superposición con el máximo valor
            horizontal_offset = 0  # Asegurar que las anotaciones estén centradas horizontalmente
            if i > 0 and saldo_dolares_filtrado[i] < saldo_dolares_filtrado[i-1]:
                vertical_offset = 10  # Ajustar posición para valores decrecientes
            axs[1].annotate(f'{txt:.2f}', (meses_dolares[i], saldo_dolares_filtrado[i]), 
                            textcoords="offset points", xytext=(horizontal_offset, vertical_offset), 
                            ha='center', color='white', bbox=dict(facecolor='black', alpha=0.7, edgecolor='none'))

    # Gráfico de Cuotas a Vencer del Mes Más Reciente
    if cuotas_recientes:
        axs[2].bar(meses_cuotas_recientes, cuotas_recientes, label='Cuotas a Vencer')
        axs[2].set_ylim(top=max(cuotas_recientes) * 1.2)  # Ajustar la escala de las barras para dar espacio a las anotaciones
        axs[2].set_title(f'Cuotas a vencer de la factura ({mes_factura_reciente})')
        axs[2].set_xlabel('Mes')
        axs[2].set_ylabel('Monto')
        axs[2].legend()

        for i, txt in enumerate(cuotas_recientes):
            vertical_offset = 10  # Colocar la anotación ligeramente por encima de la barra
            axs[2].annotate(f'{txt:.2f}', (meses_cuotas_recientes[i], txt), 
                            textcoords="offset points", xytext=(0, vertical_offset), 
                            ha='center', color='white', bbox=dict(facecolor='black', alpha=0.7, edgecolor='none'))

    if save_path:
        plt.savefig(save_path)
    plt.show()


# Obtener facturas de la carpeta
def get_files_in_folder(folder_path):
    files = []
    for root, dirs, filenames in os.walk(folder_path):
        for filename in filenames:
            if filename.endswith(".pdf"):
                files.append(os.path.join(root, filename))
    return files


# Procesar cada factura
def process_pdfs_in_folder(folder_path):
    pdf_files = get_files_in_folder(folder_path)
    conn = sqlite3.connect('invoices.db')
    cursor = conn.cursor()
    for pdf_file_path in pdf_files:
        cursor.execute('SELECT archivo FROM procesados WHERE archivo = ?', (pdf_file_path,))
        if cursor.fetchone():
            print(f"Archivo ya procesado: {pdf_file_path}")
        else:
            print(f"Procesando archivo: {pdf_file_path}")
            text = extract_text_from_pdf(pdf_file_path)
            if text:
                saldos, cuotas_a_vencer = extract_invoice_info(text)
                insert_data(saldos, cuotas_a_vencer, pdf_file_path)
    conn.close()

class InvoiceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Invoice Processor")
        self.setup_gui()
        database()

    def setup_gui(self):
        self.folder_path = tk.StringVar()
        self.save_folder = tk.StringVar()

        tk.Label(self.root, text="Carpeta de Facturas:").grid(row=0, column=0, padx=10, pady=10)
        tk.Entry(self.root, textvariable=self.folder_path, width=50).grid(row=0, column=1, padx=10, pady=10)
        tk.Button(self.root, text="Seleccionar Carpeta", command=self.select_folder).grid(row=0, column=2, padx=10, pady=10)

        tk.Label(self.root, text="Carpeta para Guardar Gráficos:").grid(row=1, column=0, padx=10, pady=10)
        tk.Entry(self.root, textvariable=self.save_folder, width=50).grid(row=1, column=1, padx=10, pady=10)
        tk.Button(self.root, text="Seleccionar Carpeta", command=self.select_save_folder).grid(row=1, column=2, padx=10, pady=10)

        tk.Button(self.root, text="Procesar Facturas", command=self.process_invoices).grid(row=2, column=1, padx=10, pady=20)
        tk.Button(self.root, text="Generar Gráficos", command=self.generate_plots).grid(row=2, column=2, padx=10, pady=20)

    def select_folder(self):
        folder = filedialog.askdirectory()
        self.folder_path.set(folder)

    def select_save_folder(self):
        folder = filedialog.askdirectory()
        self.save_folder.set(folder)

    def process_invoices(self):
        folder_path = self.folder_path.get()
        if not folder_path:
            messagebox.showerror("Error", "Seleccione una carpeta de facturas.")
            return

        process_pdfs_in_folder(folder_path)
        messagebox.showinfo("Éxito", "Facturas procesadas exitosamente.")

    def generate_plots(self):
        save_folder = self.save_folder.get()
        if not save_folder:
            messagebox.showerror("Error", "Seleccione una carpeta para guardar los gráficos.")
            return

        save_path = os.path.join(save_folder, "grafico_facturas.png")
        plot_data(save_path=save_path)
        messagebox.showinfo("Éxito", f"Gráficos generados y guardados en {save_path}.")

if __name__ == "__main__":
    root = tk.Tk()
    app = InvoiceApp(root)
    root.mainloop()

 