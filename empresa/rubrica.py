"""Requisitos visibles compartidos por evaluación y guía de mejora."""
REQUISITOS = {
    "plan_ventas": {
        "clientes": ("Clientes objetivo", "Define quién compra, su ubicación, necesidad, capacidad de pago y decisión de compra; respalda la elección con validación identificable.", "Entrevista a clientes del segmento y registra fecha, perfil, necesidad, objeciones e intención de compra sin datos personales.", "Ficha del segmento y tabla de hallazgos; distingue observación y supuesto."),
        "canales": ("Canales de venta", "Explica cómo captar, convertir y retener clientes por canal, con costos, tasas de conversión sustentadas y coherencia con el segmento.", "Diseña una prueba por canal y mide contactos, prospectos, ventas, gasto y costo de adquisición; justifica el presupuesto.", "Embudo por canal con tasas, costos, fuente de los supuestos y resultados de la prueba."),
        "acciones": ("Ejecución comercial", "Asigna actividades, responsable, frecuencia, fechas, recursos, seguimiento y contingencias; comprueba capacidad operativa.", "Construye un calendario de ejecución y explica quién hará cada actividad, cuándo y cómo corregirá desviaciones.", "Calendario con responsable, fecha, costo, indicador y regla de ajuste para cada actividad."),
        "metas": ("Metas y precios", "Cuantifica precios, unidades e ingresos por periodo, justifica conversiones y capacidad y concilia las metas con finanzas.", "Calcula ingresos = precio × unidades y unidades = prospectos × conversión; documenta supuestos y compara con capacidad disponible.", "Tabla mensual de precios, unidades, ingresos y metas por canal, con escenario adverso."),
    },
    "plan_financiero": {
        "ingresos": ("Proyección de ingresos", "Presenta precios, cantidades y calendario de ingresos consistentes con ventas; justifica estacionalidad y supuestos.", "Desglosa la proyección mensual por producto o servicio y explica cómo la demanda y capacidad sostienen las unidades.", "Tabla de ingresos por mes, producto, precio y unidades con fuentes o supuestos identificados."),
        "costos": ("Costos e inversión", "Separa inversión inicial, costos fijos y variables; incluye los costos relevantes del negocio y explica su financiamiento.", "Obtén cotizaciones, separa costos únicos y recurrentes, calcula el costo variable unitario y contrasta el total inicial con el capital.", "Presupuesto de inversión y costos, con montos, frecuencia, fecha/fuente y necesidades de financiamiento."),
        "flujo": ("Liquidez y financiamiento", "Desglosa cobros y pagos por mes, saldos y financiamiento; contempla plazos, faltantes y un escenario adverso.", "Calcula saldo final = saldo inicial + cobros − pagos; ubica déficits y documenta cómo y cuándo se financiarán.", "Flujo de caja mensual con saldo inicial/final, cobros, pagos, financiamiento y contingencia."),
        "equilibrio": ("Punto de equilibrio", "Calcula margen de contribución y punto de equilibrio con supuestos verificables, y compara con demanda y capacidad.", "Calcula margen unitario = precio − costo variable unitario; equilibrio en unidades = costos fijos / margen unitario. Explica si el margen no es positivo.", "Cálculo de equilibrio con unidades, periodo, costos y comparación con ventas y capacidad; adapta la mezcla si hay varios productos."),
    },
    "analisis_mercado": {
        "segmento": ("Segmentación y tamaño", "Delimita mercado por ubicación y perfil; estima el tamaño accesible con método, fecha, fuente y límites.", "Define segmento y zona; calcula cuántos compradores pueden atenderse y justifica el método evitando confundir mercado total con clientes alcanzables.", "Ficha del mercado y cálculo del segmento accesible con fuente, fecha y supuestos."),
        "demanda": ("Validación de demanda", "Sustenta la necesidad y disposición de compra con evidencia identificable; separa datos, estimaciones y sesgos.", "Recoge resultados de entrevistas, encuestas o una prueba comercial; describe método, fecha, muestra y límites, sin inventar resultados.", "Tabla de evidencia de demanda, método, resultados, fecha y limitaciones de la muestra."),
        "competencia": ("Competidores y alternativas", "Identifica alternativas reales para el mismo segmento y compara precios, oferta, canales y fortalezas con fuentes fechadas.", "Investiga competidores directos e indirectos y registra la fuente de cada precio o característica; explica qué alternativas elige hoy el cliente.", "Matriz comparativa de alternativas, precios, oferta, canal, fuente y fecha de consulta."),
        "diferenciacion": ("Diferenciación demostrable", "Explica una ventaja específica, relevante para el cliente, defendible y coherente con precios, costos y evidencia de demanda.", "Relaciona una necesidad validada con una ventaja medible; diseña una prueba que la compare con las alternativas y establece cómo medirla.", "Propuesta de valor con comparación, evidencia o plan de validación, costo de sostenerla y riesgos."),
    },
}


def guia_local(nombre, criterios):
    return {clave: {
        "evidencia": "El texto aportado no contiene evidencia evaluable para este criterio.",
        "brecha": "No se demuestra el requisito: " + requisito,
        "acciones": [accion, "Incorpora los resultados al plan y comprueba que coincidan con los otros dos planes. No inventes cifras o fuentes."],
        "entregable": entregable,
        "verificacion": "Comprueba que cada dato tenga fuente/fecha o esté identificado como supuesto justificado; explica riesgos y límites.",
        "ejemplo": "Estructura para completar, no evidencia: [dato real del negocio] — [fuente y fecha] — [cálculo o acción] — [resultado y limitación].",
    } for clave, (_, requisito, accion, entregable) in REQUISITOS[nombre].items()}
