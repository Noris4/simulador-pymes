"""Informes completos en PDF a partir del resultado ya guardado, sin consultar a IBM."""
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether

NOMBRES = {'plan_ventas': 'Plan de ventas', 'plan_financiero': 'Plan financiero', 'analisis_mercado': 'Análisis de mercado'}


def estilos():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle(name='TituloInforme', fontName='Helvetica-Bold', fontSize=23, leading=27, textColor=colors.HexColor('#173b65'), spaceAfter=16))
    s.add(ParagraphStyle(name='Apartado', fontName='Helvetica-Bold', fontSize=15, leading=19, textColor=colors.HexColor('#1d4ed8'), spaceBefore=15, spaceAfter=10, keepWithNext=True))
    s.add(ParagraphStyle(name='Criterio', fontName='Helvetica-Bold', fontSize=11, leading=15, textColor=colors.HexColor('#173b65'), spaceBefore=12, spaceAfter=7, keepWithNext=True))
    s.add(ParagraphStyle(name='TextoInforme', fontName='Helvetica', fontSize=9.3, leading=13.4, spaceAfter=7, splitLongWords=True))
    s.add(ParagraphStyle(name='NotaInforme', parent=s['TextoInforme'], fontSize=8, leading=11, textColor=colors.HexColor('#596b80')))
    s.add(ParagraphStyle(name='CitaInforme', parent=s['TextoInforme'], leftIndent=12, borderPadding=7, backColor=colors.HexColor('#f0f5fb')))
    return s


def seguro(texto):
    texto = str(texto).replace('\x00', '').replace('−', '-').replace('—', '-').replace('–', '-').replace('‑', '-').replace('≥', '>=').replace('≤', '<=').replace('→', '->')
    return escape(texto).replace('\n', '<br/>')


def pie(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#cbd9e9'))
    canvas.line(1.8*cm, 1.55*cm, A4[0]-1.8*cm, 1.55*cm)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#596b80'))
    canvas.drawString(1.8*cm, 1.1*cm, 'Lazuli-KPI | Evaluación orientativa')
    canvas.drawRightString(A4[0]-1.8*cm, 1.1*cm, str(doc.page))
    canvas.restoreState()


def crear_informe(resultado, nombre_empresa):
    salida = BytesIO()
    s = estilos()
    historia = []
    def par(texto, estilo='TextoInforme'):
        return Paragraph(seguro(texto), s[estilo])
    def campo(titulo, texto, estilo='TextoInforme'):
        historia.append(Paragraph('<b>' + seguro(titulo) + ':</b> ' + seguro(texto), s[estilo]))
    historia.append(par('Evaluación empresarial', 'TituloInforme'))
    historia.append(par(nombre_empresa, 'Apartado'))
    campo('Resultado', f"{resultado['calificacion']:.1f}/100 - " + ('Aprobado' if resultado['aprobado'] else 'No aprobado'))
    campo('Fecha de evaluación (UTC)', resultado.get('fecha', ''))
    campo('Versión de la rúbrica', resultado.get('version_evaluacion', ''))
    campo('Identificador', resultado.get('evaluacion_id', ''))
    historia.append(par('Este informe reproduce el resultado guardado. No acredita autenticidad de documentos ni certifica viabilidad empresarial. Las citas proceden del contenido presentado; la IA puede cometer errores.', 'NotaInforme'))
    campo('Requisitos de aprobación', '80/100 globales, al menos 80% en cada plan y ningún criterio por debajo de 3/5. Capital, sector, empleados y registro legal no aportan puntos automáticos.')
    filas = [[par('Plan'), par('Obtenido'), par('Máximo')]]
    for nombre, info in resultado['detalle_puntajes'].items():
        filas.append([par(NOMBRES.get(nombre, nombre)), par(info['puntaje_obtenido']), par(info['puntaje_maximo'])])
    tabla = Table(filas, colWidths=[10.5*cm, 3*cm, 3*cm], repeatRows=1, hAlign='LEFT')
    tabla.setStyle(TableStyle([('BACKGROUND', (0,0),(-1,0), colors.HexColor('#e8f0fc')), ('VALIGN',(0,0),(-1,-1),'TOP'), ('LINEBELOW',(0,0),(-1,-1),.5,colors.HexColor('#d4dfed')), ('LEFTPADDING',(0,0),(-1,-1),8), ('RIGHTPADDING',(0,0),(-1,-1),8), ('TOPPADDING',(0,0),(-1,-1),7), ('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    historia.append(tabla)
    if resultado.get('motivos_bloqueo'):
        historia.append(par('Motivos que impiden continuar', 'Apartado'))
        for motivo in resultado['motivos_bloqueo']:
            historia.append(par('- ' + motivo))
    estados = {'ausente': 'Información ausente', 'incompleto': 'Información incompleta', 'completo_no_verificado': 'Contenido completo; autenticidad no verificada', 'contradictorio': 'Contradicción identificada'}
    for nombre, guia in resultado.get('guia_mejora', {}).items():
        historia.append(PageBreak())
        historia.append(par(NOMBRES.get(nombre, nombre), 'TituloInforme'))
        campo('Puntaje', f"{guia['puntaje']}/{guia['maximo']}")
        detalle = resultado['detalle_puntajes'][nombre]
        campo('Diagnóstico del plan', detalle.get('motivo', ''))
        campo('Prioridad de mejora', detalle.get('mejora', ''))
        for criterio, puntos in sorted(guia['criterios'].items(), key=lambda item: item[1]):
            requisito = guia['requisitos'][criterio]
            diagnostico = guia['desglose'][criterio]
            historia.append(par(f"{requisito['titulo']} - {puntos}/5", 'Criterio'))
            campo('Qué exige la rúbrica', requisito['requisito'])
            campo('Estado del contenido', estados.get(diagnostico.get('estado'), diagnostico.get('estado', '')))
            for cita in diagnostico.get('citas', []):
                campo('Fragmento revisado - ' + NOMBRES.get(cita['campo'], cita['campo']), cita['fragmento'], 'CitaInforme')
            campo('Qué encontró la evaluación', diagnostico['evidencia'])
            campo('Justificación y faltantes', diagnostico['brecha'])
            historia.append(par('Acciones concretas', 'Criterio'))
            for numero, accion in enumerate(diagnostico['acciones'], 1):
                historia.append(par(f'{numero}. {accion}'))
            campo('Qué incorporar al plan', diagnostico['entregable'])
            campo('Cómo verificar la corrección', diagnostico['verificacion'])
            campo('Ejemplo orientativo', diagnostico['ejemplo'])
    historia.append(PageBreak())
    historia.append(par('Anexo: textos evaluados', 'TituloInforme'))
    for nombre, info in resultado['detalle_puntajes'].items():
        historia.append(par(NOMBRES.get(nombre, nombre), 'Apartado'))
        for bloque in str(info.get('valor', '')).split('\n\n'):
            historia.append(par(bloque))
    documento = SimpleDocTemplate(salida, pagesize=A4, rightMargin=1.8*cm, leftMargin=1.8*cm,
                                 topMargin=1.8*cm, bottomMargin=2*cm, title='Evaluación de ' + nombre_empresa, author='Lazuli-KPI')
    documento.build(historia, onFirstPage=pie, onLaterPages=pie)
    salida.seek(0)
    return salida
