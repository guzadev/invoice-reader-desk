
# Invoice Processor

Este proyecto es una aplicación de procesamiento de facturas en PDF que extrae información relevante como saldos y cuotas a vencer, los guarda en una base de datos SQLite, y permite generar gráficos a partir de los datos extraídos. La aplicación incluye una interfaz gráfica de usuario (GUI) construida con `tkinter`.

## Características

- **Extracción automática de texto** de archivos PDF utilizando `pdfplumber`.
- **Procesamiento de datos** con expresiones regulares (`re`) para identificar el saldo y las cuotas a vencer.
- **Almacenamiento de la información** en una base de datos SQLite.
- **Visualización de datos** mediante gráficos generados con `matplotlib`.
- **Interfaz gráfica de usuario (GUI)** que permite seleccionar carpetas, procesar facturas y generar gráficos de manera sencilla.

## Requisitos

Asegúrate de tener instaladas las siguientes dependencias antes de ejecutar el proyecto:

- Python 3.7+
- `tkinter` (preinstalado en la mayoría de las instalaciones de Python)
- `pdfplumber`
- `matplotlib`
- `sqlite3` (preinstalado en Python)

Puedes instalarlas ejecutando:

```bash
pip install pdfplumber matplotlib
```

## Instalación

1. Clona este repositorio:

```bash
git clone https://github.com/tu-usuario/invoice-processor.git
cd invoice-processor
```

2. Instala las dependencias necesarias:

```bash
pip install -r requirements.txt
```

3. Ejecuta la aplicación:

```bash
python main.py
```

## Uso

1. **Seleccionar carpeta de facturas**: Usa el botón `Seleccionar Carpeta` para elegir una carpeta que contenga archivos PDF de facturas.
2. **Procesar facturas**: Haz clic en el botón `Procesar Facturas` para extraer la información de los PDFs seleccionados y almacenarla en la base de datos.
3. **Generar gráficos**: Selecciona una carpeta para guardar los gráficos y haz clic en `Generar Gráficos`. Se generará un archivo de imagen con el gráfico en la carpeta seleccionada.

## Estructura del Proyecto

```plaintext
.
├── main.py               # Código principal de la aplicación
├── invoices.db           # Base de datos SQLite (creada automáticamente)
├── README.md             # Este archivo
├── requirements.txt      # Archivo de dependencias
└── .gitignore            # Archivos y carpetas a ignorar en Git
```

### `main.py`

Este es el archivo principal que contiene toda la lógica de la aplicación, incluyendo la interfaz gráfica, extracción de datos, procesamiento y generación de gráficos.

### `invoices.db`

Este archivo se crea automáticamente cuando se procesan facturas y almacena la información de los saldos y cuotas extraídas.

## Ejemplo de Factura

La aplicación está diseñada para procesar facturas en formato PDF que contienen:

- Un saldo actual en pesos y dólares.
- Información sobre cuotas a vencer.
  
Se utilizan expresiones regulares para identificar los patrones en los textos de las facturas.

## Contribuciones

Las contribuciones son bienvenidas. Si tienes sugerencias o mejoras, no dudes en abrir un "Issue" o hacer un "Pull Request".

1. Haz un fork del proyecto
2. Crea una nueva rama para tu función (`git checkout -b nueva-funcion`)
3. Realiza tus cambios y haz commit (`git commit -am 'Agrega nueva función'`)
4. Sube los cambios a tu rama (`git push origin nueva-funcion`)
5. Abre un Pull Request

## Licencia

Este proyecto está licenciado bajo la Licencia MIT. Consulta el archivo [LICENSE](./LICENSE) para más detalles.
