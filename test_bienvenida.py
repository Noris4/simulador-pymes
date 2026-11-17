import unittest
from app import app


class Bienvenida(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_bienvenida_tiene_dos_caminos(self):
        r = self.client.get('/')
        self.assertEqual(r.status_code,200)
        html = r.get_data(as_text=True)
        self.assertIn('Registrar empresa',html)
        self.assertIn('Explorar empresas',html)
        self.assertIn('href="/registrar-empresa"',html)
        self.assertIn('href="/directorio-page"',html)
        self.assertNotIn('id="nombre"',html)

    def test_formulario_original_sigue_disponible(self):
        r = self.client.get('/registrar-empresa')
        self.assertEqual(r.status_code,200)
        html = r.get_data(as_text=True)
        self.assertIn('id="nombre"',html)
        self.assertIn('id="fundador"',html)
        self.assertIn('href="/"',html)

    def test_solo_importadores_individuales(self):
        html = self.client.get('/parametros-page').get_data(as_text=True)
        self.assertNotIn('archivo-todos',html)
        self.assertNotIn('Importar los tres planes',html)
        for nombre in ('archivo-ventas','archivo-finanzas','archivo-mercado'):
            self.assertIn('id="'+nombre+'"',html)
        self.assertEqual(html.count('type="file"'),3)

    def test_explorar_sin_registro_y_sin_aprobacion(self):
        r = self.client.get('/directorio-page')
        self.assertEqual(r.status_code,200)
        self.assertIn('Norte Digital',r.get_data(as_text=True))
        for ruta in ('/tramitologia-page','/registro-page'):
            self.assertEqual(self.client.get(ruta).status_code,302)


if __name__ == '__main__':
    unittest.main()
