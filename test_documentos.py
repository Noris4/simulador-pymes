from io import BytesIO
import unittest
from docx import Document
from pypdf import PdfReader
from werkzeug.datastructures import FileStorage
from app import app
from empresa.documentos import importar_archivo, ErrorDocumento, separar_planes
import test_integracion as pruebas
from test_integracion import respuesta
from unittest.mock import patch
import json


class Documentos(unittest.TestCase):
    def setUp(self):
        self.caso = pruebas.Integracion()
        self.caso.setUp()
        self.client = self.caso.client
        self.id = self.caso.id

    def docx(self, completo=False):
        doc = Document()
        if completo:
            for titulo in ('Plan de ventas','Plan financiero','Análisis de mercado'):
                doc.add_heading(titulo, level=1)
                doc.add_paragraph('Texto suficientemente largo para este apartado de la empresa.')
                tabla = doc.add_table(rows=1, cols=2)
                tabla.cell(0,0).text = 'Mes 1'
                tabla.cell(0,1).text = '8000'
        else:
            doc.add_paragraph('Plan de ventas con datos de clientes y canales comerciales.')
        archivo = BytesIO()
        doc.save(archivo)
        archivo.seek(0)
        return archivo

    def test_word_individual_y_tablas_en_orden(self):
        r = self.client.post(f'/empresa/{self.id}/importar-documento', data={'campo':'plan_ventas','archivo':(self.docx(),'ventas.docx')})
        self.assertEqual(r.status_code, 200)
        self.assertIn('clientes y canales', r.get_json()['campos']['plan_ventas'])
        r = self.client.post(f'/empresa/{self.id}/importar-documento', data={'campo':'todos','archivo':(self.docx(True),'expediente.docx')})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.get_json()['campos']), 3)
        self.assertIn('Mes 1 | 8000', r.get_json()['campos']['plan_financiero'])

    def test_pdf_unico_separa_tres_planes(self):
        from pathlib import Path
        archivo = Path(__file__).resolve().parent / 'ejemplos/norte-continuo/Norte-Continuo-TI.pdf'
        with archivo.open('rb') as f:
            campos = importar_archivo(FileStorage(stream=f,filename='expediente.pdf'), 'todos')
        self.assertEqual(set(campos), {'plan_ventas','plan_financiero','analisis_mercado'})
        self.assertIn('NC-VALIDACION-02', campos['analisis_mercado'])
        self.assertIn('170000', campos['plan_financiero'].replace(',',''))
        self.assertLessEqual(max(map(len,campos.values())),12000)
        with archivo.open('rb') as f:
            solo_finanzas = importar_archivo(FileStorage(stream=f,filename='expediente.pdf'),'plan_financiero')
        self.assertEqual(set(solo_finanzas),{'plan_financiero'})
        self.assertNotIn('NC-VALIDACION-02',solo_finanzas['plan_financiero'])

    def test_documentos_invalidos_y_sin_titulos(self):
        for nombre in ('prueba.doc','prueba.exe','prueba.pdf','prueba.docx'):
            with self.subTest(nombre=nombre), self.assertRaises(ErrorDocumento):
                importar_archivo(FileStorage(stream=BytesIO(b'archivo invalido'),filename=nombre), 'todos')
        with self.assertRaises(ErrorDocumento):
            separar_planes('Texto sin encabezados de los tres planes.')

    def test_sin_sesion_no_se_puede_importar(self):
        visitante = app.test_client()
        self.assertEqual(visitante.post(f'/empresa/{self.id}/importar-documento', data={}).status_code,403)

    def test_informe_pdf_de_reprobado_incluye_desglose(self):
        with patch('empresa.revision_planes.llamar_chat', return_value=json.dumps(respuesta(2))):
            evaluacion = self.client.post(f'/empresa/{self.id}/evaluar').get_json()
        self.assertFalse(evaluacion['aprobado'])
        url = f"/empresa/{self.id}/evaluaciones/{evaluacion['evaluacion_id']}/pdf"
        r = self.client.get(url)
        self.assertEqual(r.status_code,200)
        self.assertIn('attachment', r.headers['Content-Disposition'])
        lector = PdfReader(BytesIO(r.data))
        texto = '\n'.join(p.extract_text() for p in lector.pages)
        for valor in ('No aprobado','Acciones concretas','Anexo: textos evaluados','Cómo verificar la corrección'):
            self.assertIn(valor,texto)
        self.assertEqual(app.test_client().get(url).status_code,403)
        self.assertEqual(self.client.get(f'/empresa/{self.id}/evaluaciones/inexistente/pdf').status_code,404)


if __name__ == '__main__':
    unittest.main()
