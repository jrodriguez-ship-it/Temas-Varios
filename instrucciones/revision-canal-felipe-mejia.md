Necesito que revises a fondo los videos más importantes del canal de YouTube de Felipe Mejía M. (https://www.youtube.com/@felipemejiam, finanzas corporativas, modelaje financiero, valoración, análisis financiero, unos 162 videos) y que saques de ellos las buenas prácticas que puedo aplicar en mi trabajo financiero en DISEX: qué ya hago bien, qué puedo aplicar nuevo y qué debo mejorar en análisis e informes financieros para la toma de decisiones de la empresa.

## Contexto: lo que hago hoy en DISEX

- Cada mes preparo los estados financieros de DISEX para el comité de crédito del banco (PDF A4). Tienen portada; resumen con cifras principales e indicadores de liquidez, endeudamiento y rentabilidad comparados con el mes anterior; balance (activos; pasivos y patrimonio); estado de resultados con columnas MES y ACUMULADO; anexos de ingresos no operacionales, gastos de administración, gastos de venta y otros gastos; firmas.
- Las cifras salen de un Excel contable (balance y PyG en miles; anexos en pesos). Hago cruces: Activo = Pasivo + Patrimonio, utilidad del balance = utilidad del PyG acumulado, anexos = líneas del PyG.
- Hoy el informe NO incluye flujo de efectivo, capital de trabajo ni días de rotación (cartera, inventario, proveedores), EBITDA, EVA o ROIC vs. costo de capital, proyecciones, comparación contra presupuesto, sensibilidades ni un tablero ejecutivo para la gerencia o junta.
- Si en mi computador hay ejemplos de estos informes o del Excel fuente, pregúntame dónde están antes de buscarlos. No los modifiques.

## Paso 1: obtener las transcripciones (bloqueante)

1. Intenta primero con `yt-dlp` (`pip install yt-dlp`) para bajar solo los subtítulos, sin el video:
   `yt-dlp --skip-download --write-auto-subs --write-subs --sub-langs "es.*,es" --sub-format vtt -o "transcripciones/%(id)s.%(ext)s" <URL>`
   Si no funciona, usa `youtube-transcript-api` en Python. Si tampoco, abre los videos en Chrome (Claude in Chrome) y lee la transcripción desde "Mostrar transcripción".
2. Limpia cada VTT a texto plano (sin marcas de tiempo duplicadas). Conserva marcas de tiempo cada ~2 minutos para poder citar.
3. Guarda todo en una carpeta `revision-felipe-mejia/transcripciones/`.
4. Si un video no tiene subtítulos, dímelo y sigue con los demás. Solo transcribe el audio con Whisper si te lo autorizo.
5. Antes de analizar, refresca el catálogo del canal (`yt-dlp --flat-playlist` sobre `/videos` y sobre las listas) por si hay videos nuevos relevantes. Sugiéreme si alguno debería entrar en la lista.

## Paso 2: videos a revisar (en este orden de prioridad)

**Prioridad 1: análisis e informe mensual**
- PqM9x_USZb4 · ¿Cómo realizar un análisis financiero? Taller práctico (45 min)
- F8CwkzklN38 · ¿Cuáles son los principales indicadores en un análisis financiero? (11 min)
- PjJVtNqSmmQ · Claude Dashboard de Junta Directiva (4 min)
- _6CT_4BKeXc · Clase 3. Análisis financiero Parte 3 (Liquidez y Cambio en Capital de trabajo) (44 min)
- 711t87n8Yds · Introducción al Análisis financiero (6 min)
- GszyhOzc34Q · Indicadores de rentabilidad (6 min)
- RzImoygZmSg · Indicadores de Solvencia (4 min)
- axYM_KCf9IQ · Indicadores de Liquidez (4 min)
- ub95tFyr7uo · Indicadores de generación de valor (4 min)
- Mn5sWd1iNt8 · Análisis financiero. Flujo de efectivo (6 min)

**Prioridad 2: flujo de efectivo y herramientas con Claude**
- ht3_1YIJBGo · ¿Cómo construir un Flujo de Efectivo? (8 min)
- Lista "Gestión de flujo de caja" (1/6 a 6/6): wPxynkOngb4, EroiG1wrTTA, QxBGag2shaE, G233ckohc0s, KfOrGp7YzVk, PJjRdxq0uzU
- pyGvj-G4nzo · Diversos flujos de efectivo en Modelación y planeación financiera (15 min)
- 6OJfevYjVoQ · Claude EBITDA · MDiwIOmGBmM · Claude Flujo de efectivo · yRUNXPeEGCA · Claude Cálculo de indicadores de rotación · zTL__4Iw39U · Claude Gráficas · K52qReNQY4k · Claude Matriz de depreciación
- NDDy1waM31w, Ko4Z7urUdqQ, YoI8u_5AJfk · Análisis financiero y planeación de empresa de restaurantes I, II y III (caso aplicado)

**Prioridad 3: planeación, proyección y generación de valor**
- 6YmUSkegw7I · Modelación de aumento de inventarios y cartera (2 h 10 min)
- lBPRDaqNdNs · Análisis de Capex y proyección de PP&E sobre ingresos (21 min)
- N1NUeb7xAnk · Cierre de Balance General. Aumento de Patrimonio y Utilidades retenidas (38 min)
- ZAf9kcio2nI · Modelación de crédito Rollover (1 h 58 min) y _UdOCnYfwew · ¿Cómo modelar el crédito de tesorería Rollover? (8 min)
- l_TZ6-a56L0 · Rentabilidad con y sin apalancamiento (2 h 17 min)
- 69FsBhrZYFE · Cálculo de EVA con Rolling WACC (8 min)
- vYGZIlO0FTc · ¿Cómo construir un WACC en Colombia? (29 min) y g8EVTgSzh9k · Cálculo de WACC con Claude Add-in en Excel (29 min)
- wwT-Px5LVWc · Reestructuración financiera de empresas (1 h 55 min)
- SQGzwMgLbCk · Valoración de empresas y sensibilidades (1 h 42 min)
- 0gMGM77BCuY · Clase 1. Modelaje financiero Intensivo (1 h 52 min) y 2ynHf6ut2X8 · Caso 5. Modelaje financiero (2 h 14 min, el más reciente)

URL de cada video: https://www.youtube.com/watch?v=<ID>

## Paso 3: análisis

Usa subagentes en paralelo, por ejemplo uno por grupo de videos. Para cada video, que el subagente devuelva:
- Resumen de 5–8 líneas.
- Las prácticas, métodos, fórmulas, indicadores y criterios de interpretación concretos que enseña, cada uno con su marca de tiempo (mm:ss).
- Advertencias o errores comunes que señala.
- Cómo usa Claude o Excel, si aplica: prompts, estructura y formato.

Luego consolida tú y cruza todo contra lo que hago hoy en DISEX (sección de contexto). Reglas:
- Todo lo que atribuyas a Felipe Mejía debe venir de una transcripción y llevar la cita (video + marca de tiempo). Si agregas algo de tu cosecha, márcalo como "[recomendación propia, no del canal]".
- Nada inventado. Si un tema no aparece en los videos, dilo.
- Piensa en un lector que es un banco (comité de crédito) y en la gerencia de DISEX que toma decisiones: liquidez, capacidad de pago, generación de caja, cobertura de deuda, capital de trabajo.

## Paso 4: entregable

Un informe en español en `revision-felipe-mejia/`, en Markdown y en Word (.docx), con:
1. **Resumen ejecutivo** (1 página): las 10 mejoras de mayor impacto, ordenadas.
2. **Lo que ya hago bien**, validado por el canal.
3. **Lo que debo aplicar nuevo**: por ejemplo flujo de efectivo indirecto, capital de trabajo y ciclo de caja, EBITDA y su conversión en caja, cobertura de deuda, EVA o ROIC vs. WACC, tablero de junta. Cada punto con: qué es, por qué le importa al banco o a la gerencia, fórmula exacta, de qué líneas del balance o PyG sale, cómo se interpreta, y la cita del video.
4. **Lo que debo mejorar** en el informe actual: estructura, narrativa, gráficas, comparativos (mes anterior, mismo mes del año anterior, presupuesto), análisis vertical y horizontal, comentarios de variaciones.
5. **Propuesta de nueva estructura del informe mensual**, página por página. Separa la versión para el banco de la versión para la gerencia o junta.
6. **Plan de implementación** en 3 fases (inmediato / 1–3 meses / 3–6 meses), con qué datos adicionales necesito pedirle a contabilidad.
7. **Prompts o instrucciones de Claude reutilizables** que el canal muestre o que se deriven de él, para automatizar indicadores, flujo de efectivo y tablero.
8. **Anexo**: tabla de videos revisados (ID, título, duración, transcripción sí/no) y fichas por video.

## Paso 5: control de calidad

Antes de entregarme, lanza un subagente nuevo que no vea tu razonamiento. Debe:
- Tomar una muestra de al menos 15 afirmaciones atribuidas al canal y verificarlas contra las transcripciones.
- Revisar que las fórmulas sean correctas.
- Revisar que las recomendaciones sean aplicables a una empresa colombiana como DISEX.

Corrige lo que encuentre. Al final dame un resumen de 5 líneas: videos revisados y faltantes, las 3 mejoras más importantes, y dónde quedaron los archivos.

No modifiques ningún archivo existente de mi computador; trabaja solo dentro de `revision-felipe-mejia/`.
