# Revisión interna del proyecto — 26 de julio de 2026

**Tarea:** revisión de notebooks (claridad y lógica) y del aplicativo (fallos y lógica),
según el plan de acción ("Validación cruzada de notebooks", responsable: Iván Cristancho).
**Alcance revisado:** notebooks 01–08, `dashboard/dashboard_auditoria.html`,
`documentacion/SICortex_Panel_2.html`, README, datos y artefactos de `outputs/`.

---

## 1 · Hallazgos de datos y lógica

### 1.1 Registro de prueba interno `ATN-JEF-000001` (integridad referencial) — DOCUMENTADO
`hc_detalle` trae 2 filas (`DET-0003057`, `DET-0003058`: Consulta médica general 890205 y
Hemograma 902201, 15-jun-2025, MED-001) que apuntan a una atención **que no existe** en
`atenciones`. Viene así desde `data/raw/`. Consecuencias que nadie había conectado:

- El notebook 01 la registró (`fk_atenciones_rotas: 2` en `limpieza_reporte.json`) pero su
  "verificación de cierre" pedía 0 FK rotas y el resumen impreso no mostraba FKs → pasó inadvertida.
- El notebook 02 reportaba **1.201 atenciones** (1.200 reales + esta).
- Los 2 códigos `SOLO_HC` del notebook 03 son exactamente estas 2 filas — no son "fuga sistemática".

**Origen identificado (revisión cruzada con el aplicativo, 26-jul):** es un **dato de prueba
interno del equipo** — la atención demo del paciente `1005711681` que usa LINE
(`agregar_paciente_prueba.py` y `data/datos_prueba/prefacturas/1005711681/` del repositorio del
aplicativo). **No es un hallazgo para Health & Life y no debe escalarse al cliente.**

**Acción tomada:** se documentó como dato de prueba en los notebooks 01, 02 y 03 y en el
dashboard (nueva columna "FKs rotas" + nota). **Se conservan las filas** para no alterar los
insumos de `data/raw/`; en una carga con datos reales deben excluirse junto con el resto de los
datos de prueba.

### 1.2 Pérdida por fugas subestimada y mal calculada — CORREGIDO
El notebook 04 estimaba la pérdida como `152 × promedio(valor_unitario)` donde el promedio
**incluía los ceros imputados de las propias fugas** (y de los ítems sin prefactura):

| Método | Pérdida estimada |
|---|---|
| Anterior (promedio con ceros) | $41,571,660 |
| Promedio simple de ítems facturados (cota conservadora) | $43,696,371 |
| **Precio de referencia por CUPS × cantidad realizada (nuevo método principal)** | **$78,046,000** |

Las fugas se concentran en códigos de alto valor, por eso la diferencia casi duplica la cifra.
El notebook 04 ahora imprime el detalle por código CUPS.
⚠️ **Pendiente del equipo:** actualizar la cifra en el informe técnico (.docx), la presentación
(.pptx) y el guion del video. README y dashboard ya quedaron actualizados.

### 1.3 Tres versiones de métricas del CNN conviven en el repo — PARCIALMENTE CORREGIDO
| Fuente | AUC | Origen |
|---|---|---|
| README / dashboard / `metrics.json` ("referencia") | 0.7487 | corrida original del equipo |
| Notebook 08 (outputs guardados en el repo) | 0.6984 | corrida comiteada |
| `outputs/models/cnn/metrics_fase2.json` (huérfano) | 0.7104 | otra corrida, sin notebook que lo genere |

Además, el dashboard y `metrics.json` decían que el CNN "no es re-ejecutable en esta copia
(SavedModel incompleto, sin .h5)" — **falso en este repo**: los binarios están en
`outputs/models/cnn/` y el notebook 08 los regenera completos.

**Acción tomada:** textos corregidos en nb 05/06 y dashboard (ahora dice "corrida de referencia
del equipo" y avisa la discrepancia). El nb 08 ganó una celda que exporta `metrics_fase2.json`
(los huérfanos tendrán dueño en la próxima corrida).
⚠️ **Pendiente del equipo:** re-ejecutar el nb 08 completo y **consolidar una sola cifra de CNN**
en README, nb 05 y dashboard.

> **Actualización (26-jul, noche):** una re-ejecución completa del nb 08 en copia aislada
> (Python 3.12, TF 2.16.1) dio **AUC 0.6954 con umbral óptimo 0.4194** — el mismo clúster ~0.70
> de las demás corridas del notebook, lejos del 0.7487 citado como referencia.

### 1.4 Notebook 07 comiteado con corrida sucia — PARCIALMENTE CORREGIDO
- La celda de cross-validation quedó guardada con un **`KeyboardInterrupt`**.
- El SHAP falló por incompatibilidad de versiones y aún así se guardaba el explainer:
  **`shap_explainer_xgboost.pkl` del repo es literalmente un `None` serializado** (verificado).
- La tabla final "Resultados Esperados" tenía cifras de una corrida anterior (threshold 0.793,
  FP=7…) que contradicen los outputs del propio notebook (threshold 0.896, FP=1).
- `cv_results.json` era huérfano (ninguna celda lo generaba).

**Acción tomada:** tabla final sincronizada con la corrida real; el guardado del explainer ahora
se omite (y borra el pickle viejo) si SHAP falla; la celda de CV exporta `cv_results.json`.
⚠️ **Pendiente del equipo:** re-ejecutar el nb 07 de punta a punta (kernel limpio) para dejar
outputs coherentes; verificar que SHAP funcione con las versiones actuales.

> **Actualización (26-jul, noche):** verificado en copia aislada — con Python 3.12 y los pines de
> `requirements.txt` el nb 07 corre completo: la validación cruzada termina sin interrupción,
> **SHAP funciona** (explainer real + `shap_summary.png`) y el umbral 0.896 con todas sus
> métricas se reproducen exactos. Basta re-ejecutarlo en ese entorno.

### 1.5 Umbral "óptimo" elegido sobre el test set (nb 05, 07 y 08) — DOCUMENTADO
Los tres notebooks buscan el threshold que maximiza F1 **usando las etiquetas del test set** y
reportan métricas sobre ese mismo test → las métricas "en el umbral óptimo" son optimistas.
Además el criterio no es consistente (recall ≥ 0.85 en nb 05, ≥ 0.55 en nb 07, ≥ 0.55/0.6 en nb 08).
Se dejó constancia en los tres notebooks; se mantuvo el cálculo por comparabilidad. Si hay tiempo
antes de la entrega, lo riguroso es elegir el umbral por validación (o CV en train) y solo
*reportar* en test — y unificar el criterio de recall mínimo.

### 1.6 Otras observaciones menores (corregidas)
- Dashboard mostraba **4 de los 6 hallazgos del EDA** (el `eda_hallazgos.md` comiteado venía de
  una corrida parcial del nb 04) → re-ejecutado, ahora 6.
- Cierre del nb 05 citaba "AUC ≈ 0.901" que no corresponde a ningún resultado (real: 0.9152).
- Referencias muertas: `docs/AUDIT_PROYECTO.md`, carpeta `health_care_claude/`,
  `04_NOTEBOOKS/02_modelo_cnn...` → eliminadas/corregidas.
- README: comando de clonado roto, tabla de umbrales atribuía a XGBoost una fila que es de
  Random Forest, faltaban `dashboard/` en la estructura, TensorFlow en las dependencias,
  `LICENSE` (se menciona MIT y no existía) y `requirements.txt` → todo corregido/creado.
- KPIs del dashboard tenían los porcentajes 79.2/20.8 *hardcodeados* → ahora dinámicos.
- nb 04 contaba 16 PNG y decía "deben existir 10" (contaba también las figuras del nb 05) →
  ahora cuenta solo las 10 del EDA.

## 2 · Notebooks: claridad y narrativa

- **01–06:** bien narrados (contexto, entradas/salidas, decisiones justificadas, verificación
  de cierre). Solo se les agregaron las notas de los hallazgos anteriores.
- **07:** estructura aceptable pero seca; se agregó una introducción ("¿por qué un segundo
  XGBoost?" — GridSearch + SHAP + umbral operativo + artefactos de inferencia, y por qué su AUC
  difiere del nb 05) y notas metodológicas.
- **08:** tenía **una sola celda de markdown** en todo el notebook. Se agregaron 11 secciones
  narradas (features y leakage, split sin fuga, conversión tabular→imagen con su advertencia de
  colisiones en el grid, arquitectura y focal loss, fases 1/2 con los fixes explicados, umbral,
  guardado, inferencia) + verificación de cierre al estilo de los demás.

## 3 · Aplicativo

### 3.1 `dashboard/dashboard_auditoria.html` (generado por nb 06)
Corregido y regenerado: hallazgos completos (6), columna FKs rotas + nota de la atención
fantasma, nota de los códigos SOLO_HC, fila CNN re-etiquetada con aviso de consolidación,
sección de reproducibilidad sin referencias muertas, KPI de pérdida actualizado.

### 3.2 `documentacion/SICortex_Panel_2.html` (panel de tareas del equipo)
- **Persistencia:** usaba `window.storage`, que **solo existe publicado como artifact de
  Claude**; abierto como archivo local no guardaba nada (y el texto prometía "guardado para
  todo el equipo"). → Ahora cae a `localStorage` (guardado por navegador) y el texto lo aclara.
- **Tareas eliminadas resucitaban** al recargar (las 40 base están hardcodeadas y el borrado no
  se persistía). → Se persiste `__deleted`.
- **Días de la semana de la "Semana 0" estaban corridos** (pintaba el 08-jul como LUN; es MIÉ).
  → Corregido con `dowOffset`.

### 3.3 El aplicativo principal NO está en el repo ⚠️
Según el propio panel de tareas, existen `server.py` (backend + endpoints), `index.html`/`app.js`
(frontend), pipeline de inferencia e integración de NVIDIA Nemotron (Jefersson e Isabella).
**Nada de eso está en este repositorio** — no se pudo auditar. Si la entrega incluye el
aplicativo, hay que subirlo al repo (y ahí puede revisarse end-to-end).

## 4 · Checklist antes de la entrega (04-ago)

1. [ ] Subir el aplicativo (server.py, frontend, Nemotron) al repo y revisarlo.
2. [ ] Re-ejecutar nb 07 y nb 08 de punta a punta (kernel limpio) en el entorno del equipo.
3. [ ] Consolidar la cifra del CNN (README, nb 05, dashboard) tras re-ejecutar el 08.
4. [ ] Re-ejecutar nb 05 → 06 para refrescar `metrics.json` (textos) y el dashboard.
5. [ ] Actualizar la pérdida estimada ($78.0M / cota $43.7M) en informe .docx, .pptx y video.
6. [ ] Preguntar a Health & Life por el código inventado `890201-M`. (`ATN-JEF-000001` **no** va
   en esa consulta: ya está identificado como dato de prueba interno del equipo — §1.1.)
7. [ ] (Opcional, si hay tiempo) Umbral elegido por validación en vez del test set, y criterio
   de recall mínimo unificado entre notebooks.

---
*Revisión hecha con apoyo de Claude Code sobre el repo `jaoliverosm/Capstone-` (commit `e8712af`).*
