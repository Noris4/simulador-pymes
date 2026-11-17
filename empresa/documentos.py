"""Extracción local de PDF con texto y Word .docx, sin conservar archivos subidos."""
from io import BytesIO
from pathlib import Path
import re
import unicodedata
from zipfile import ZipFile, BadZipFile

MAX_ARCHIVO = 10 * 1024 * 1024
MAX_TEXTO = 60000
MAX_PLAN = 12000
CAMPOS = ('plan_ventas', 'plan_financiero', 'analisis_mercado')


class ErrorDocumento(ValueError):
    pass


def extraer_texto(archivo):
    extension = Path(archivo.filename or '').suffix.lower()
    if extension not in {'.pdf', '.docx'}:
        raise ErrorDocumento('Selecciona un PDF o un Word .docx. Si tienes un .doc, guárdalo primero como .docx.')
    datos = archivo.stream.read(MAX_ARCHIVO + 1)
    if not datos or len(datos) > MAX_ARCHIVO:
        raise ErrorDocumento('El archivo está vacío o supera el límite de 10 MB.')
    try:
        partes = []
        if extension == '.pdf':
            from pypdf import PdfReader
            if not datos.startswith(b'%PDF-'):
                raise ErrorDocumento('El archivo seleccionado no es un PDF válido.')
            lector = PdfReader(BytesIO(datos))
            if lector.is_encrypted:
                raise ErrorDocumento('El PDF tiene contraseña. Sube una copia sin protección.')
            if len(lector.pages) > 80:
                raise ErrorDocumento('El documento no puede superar 80 páginas.')
            for pagina in lector.pages:
                partes.append(pagina.extract_text() or '')
                if sum(map(len, partes)) > MAX_TEXTO:
                    raise ErrorDocumento('El documento contiene demasiado texto. Divide o resume los planes.')
        else:
            from docx import Document
            from docx.table import Table
            from docx.text.paragraph import Paragraph
            with ZipFile(BytesIO(datos)) as paquete:
                miembros = paquete.infolist()
                if len(miembros) > 2000 or sum(i.file_size for i in miembros) > 30 * 1024 * 1024:
                    raise ErrorDocumento('El Word es demasiado grande al descomprimirlo.')
                if 'word/document.xml' not in paquete.namelist():
                    raise ErrorDocumento('El archivo no contiene un documento Word válido.')
            documento = Document(BytesIO(datos))
            # Conserva el orden de párrafos y tablas, incluidos los escenarios financieros.
            for bloque in documento.iter_inner_content():
                if isinstance(bloque, Paragraph):
                    partes.append(bloque.text)
                elif isinstance(bloque, Table):
                    partes.append('\n'.join(' | '.join(c.text for c in fila.cells) for fila in bloque.rows))
                if sum(map(len, partes)) > MAX_TEXTO:
                    raise ErrorDocumento('El documento contiene demasiado texto. Divide o resume los planes.')
        texto = '\n\n'.join(p.strip() for p in partes if p.strip()).replace('\x00', '').strip()
    except ErrorDocumento:
        raise
    except Exception:
        raise ErrorDocumento('No se pudo leer el documento. Comprueba que no esté dañado o protegido.') from None
    if len(texto) < 10:
        raise ErrorDocumento('No se encontró texto legible. Si el PDF es un escaneo, conviértelo primero a texto mediante OCR.')
    if len(texto) > MAX_TEXTO:
        raise ErrorDocumento('El documento contiene demasiado texto.')
    return texto


def separar_planes(texto):
    # Solo encabezados completos en una línea; una mención dentro de un párrafo no divide el plan.
    encabezado = re.compile(r'^\s*(?:\d+[.)\-]?\s*)?(plan de ventas|plan financiero|an[aá]lisis de mercado)\s*:?\s*$', re.I | re.M)
    encontrados = list(encabezado.finditer(texto))
    equivalencias = {'plan de ventas': 'plan_ventas', 'plan financiero': 'plan_financiero', 'analisis de mercado': 'analisis_mercado'}
    resultado = {}
    for i, coincidencia in enumerate(encontrados):
        titulo = ''.join(c for c in unicodedata.normalize('NFD', coincidencia[1].lower()) if unicodedata.category(c) != 'Mn')
        campo = equivalencias[titulo]
        if campo in resultado:
            raise ErrorDocumento('Cada encabezado debe aparecer una sola vez. Quita el índice o los encabezados repetidos del documento.')
        fin = encontrados[i + 1].start() if i + 1 < len(encontrados) else len(texto)
        contenido = texto[coincidencia.end():fin].strip()
        if not 10 <= len(contenido) <= MAX_PLAN:
            raise ErrorDocumento(f'{coincidencia[1]} debe contener entre 10 y {MAX_PLAN} caracteres. No se recorta automáticamente.')
        resultado[campo] = contenido
    if set(resultado) != set(CAMPOS):
        raise ErrorDocumento('Para importar los tres planes usa estos títulos, cada uno en su propia línea: Plan de ventas, Plan financiero y Análisis de mercado.')
    return resultado


def importar_archivo(archivo, campo):
    texto = extraer_texto(archivo)
    if campo == 'todos':
        return separar_planes(texto)
    if campo not in CAMPOS:
        raise ErrorDocumento('Selecciona un apartado válido para importar.')
    try:
        planes = separar_planes(texto)
    except ErrorDocumento:
        planes = None
    if planes is not None:
        return {campo: planes[campo]}
    if len(texto) > MAX_PLAN:
        raise ErrorDocumento('Este apartado supera 12000 caracteres. Sube solo el plan correspondiente o usa un documento con los títulos de los tres planes en líneas independientes.')
    return {campo: texto}
