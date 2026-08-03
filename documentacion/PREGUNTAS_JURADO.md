# 🎓 Preguntas Probables del Jurado — LINE Auditor Médico Digital

> **Material interno de preparación** para la sustentación del Capstone SIC 2025.
> Organizado por categorías: producto/negocio, técnica (modelos), datos, cumplimiento normativo y decisiones de diseño.
> Cada respuesta incluye el dato concreto para respaldarla (métricas, archivos, endpoints).

---

## 1. 🏥 Producto y Negocio

### P1. ¿Qué problema resuelve LINE?
**Respuesta:** En las IPS, los servicios realizados no siempre se facturan, los códigos CUPS se transcriben mal y las cantidades no coinciden con la Historia Clínica. Cada inconsistencia se traduce en glosas, devoluciones y fugas de ingreso. LINE audita automáticamente cada prefactura: cruza los ítems facturados contra la HC real, valida la afiliación en la BDUA (ADRES) y prioriza los casos de mayor impacto para el auditor.

### P2. ¿Cuánto dinero puede recuperar la IPS con esto?
**Respuesta:** En los 3,126 cruces del dataset encontramos **152 procedimientos con soporte clínico sin facturar (fugas)**. Valoradas con el precio de referencia de su CUPS × cantidad realizada, representan una **pérdida estimada de $78,046,000 COP**; con una cota conservadora (promedio simple de ítems facturados, $287,476), **$43,696,371 COP**. El módulo Capstone documenta el detalle por código CUPS en el notebook 04.

### P3. ¿Quién es el usuario final?
**Respuesta:** El equipo auditor de la IPS (Health & Life IPS SAS). El flujo pensado: el auditor sube la prefactura (CSV o PDF), LINE cruza contra la HC, y el sistema le entrega una recomendación (APROBAR / REVISAR / RECHAZAR) con el detalle de cada hallazgo para que el auditor decida con evidencia, no a mano.

### P4. ¿Por qué no basta con reglas simples?
**Respuesta:** Las reglas (cuando el cruce es perfecto) son casi deterministas, pero el valor real está en (1) **priorizar por probabilidad** cuando hay miles de cruces, (2) **generalizar** ante datos incompletos o mal tipeados, y (3) **explicar** con un modelo (SHAP) qué feature pesa en cada caso. Además el Capstone exige transfer learning (CNN), que es la parte de IA profunda del proyecto.

---

## 2. 🤖 Técnica — Modelos

### P5. ¿Qué modelos usan y cuál es el de producción?
**Respuesta:** Tres familias:
| Modelo | Escenario | AUC-ROC | F1 | Precisión | Umbral |
|--------|-----------|---------|-----|-----------|--------|
| **XGBoost ⭐ (producción)** | A: features tabulares | **0.8983** | **0.7864** | **99.2%** | 0.896 |
| Random Forest | A: features tabulares | 0.9185 | 0.7346 | 92.3% | 0.50 |
| Random Forest | B: features del CNN | 0.8500 | 0.6138 | 93.7% | 0.50 |
| XGBoost | B: features del CNN | 0.8707 | 0.6799 | 75.9% | 0.50 |
| CNN MobileNetV2 | B: features del CNN | 0.6727 | 0.4264 | 34.3% | 0.4273 |

**En producción está el XGBoost del notebook 07** (AUC 0.8983, F1 0.7864, precisión 99.2% con umbral 0.896). El Random Forest tiene mayor AUC bruto (0.9185) pero menor precisión; elegimos XGBoost por el mejor balance F1/precisión (mínimos falsos positivos).

### P6. ¿Por qué incluyen un CNN si rinde peor que XGBoost?
**Respuesta:** Tres razones: (1) el **Capstone exige transfer learning** como técnica de IA profunda; (2) en el escenario B (mismas features) XGBoost supera al CNN, lo que demuestra que la comparación es honesta y que el techo realista para datos tabulares lo marcan los modelos clásicos; (3) el pipeline tabular→imagen (t-SNE a grid 32×32 + MobileNetV2) es un experimento válido de investigación. Lo reportamos con cifras reproducibles (0.6727, ±0.02 en CPU), no con la referencia histórica 0.7487 que no era reproducible.

### P7. ¿Qué features usan? ¿Cómo evitan el leakage?
**Respuesta:** 23 numéricas (edad, cantidades realizada vs facturada, valores, días entre atención y facturación, proporciones de CUPS con/sin soporte) y 13 categóricas (sexo, tipo de documento, afiliación, ciudad, EPS, sede, CIE-10, médico). **Excluimos por leakage** las salidas directas del sistema de reglas (`resultado`, `tipo_alerta`, `severidad`, `descripcion_alerta`) y flags equivalentes al target a nivel de fila. En el EDA los usamos solo como descriptores.

### P8. ¿Cómo manejan el desbalance del target?
**Respuesta:** 79.2% consistentes vs 20.8% inconsistentes. Lo manejamos con `scale_pos_weight` en XGBoost, ajuste de threshold óptimo (0.896 para producción) y validación cruzada 5-fold estratificada. El threshold se puede ajustar según el costo relativo de falsos positivos vs falsos negativos.

### P9. ¿Qué es el pipeline tabular → imagen del CNN?
**Respuesta:** (1) imputación de nulos, (2) escalado con StandardScaler, (3) one-hot encoding → 111 features dummy, (4) mapeo a grid 32×32 vía t-SNE, (5) normalización global min-max, (6) CNN MobileNetV2 (transfer learning) → probabilidad de inconsistencia. Todo parametrizado en `artefactos_preprocesamiento.pkl`.

---

## 3. 🧠 Arquitectura de la Aplicación

### P10. ¿Cómo funciona la app de punta a punta?
**Respuesta:** 1) el usuario sube CSV/PDF de prefactura; 2) se verifica la afiliación en la BDUA vía ADRES (web scraping de consulta ciudadana, con **modo contingencia** si ADRES no responde 403/captcha/timeout); 3) cruce HC vs PF por código CUPS y atención (detecta SIN_SOPORTE_CLINICO, CODIGO_NO_COINCIDE, CANTIDAD_DISCORDANTE, CONSISTENTE, NO_FACTURADO); 4) modelos opcionales CNN local, XGBoost local y/o Nemotron externo; 5) resultado consolidado con recomendación jerárquica (RECHAZAR > REVISAR > APROBAR) y detalle por cruce. Frontend Tailwind + JS, backend FastAPI, BD SQLite.

### P11. ¿Por qué FastAPI y no Flask/Django?
**Respuesta:** FastAPI ofrece validación de tipos automática, documentación interactiva `/docs`, async nativo y rendimiento alto con Uvicorn; ideal para un backend de inferencia de ML con varios endpoints. Flask no trae la documentación interactiva de serie y Django sería sobredimensionado para una API de inferencia local.

### P12. ¿Qué hace el modelo externo Nemotron?
**Respuesta:** Es un LLM de NVIDIA (vía API) que recibe el contexto clínico completo (diagnóstico, ítems PF, ítems HC, cruces) y genera un **análisis explicativo con razonamiento clínico**, como alternativa al pipeline local. Es opcional (requiere `NVIDIA_API_KEY`); el sistema funciona 100% local con XGBoost + CNN.

### P13. ¿Cómo garantizan que funcione en la máquina del jurado?
**Respuesta:** `start.bat` (Windows) y `start.py` (multiplataforma) detectan Python, verifican los modelos (`auditor_medico_cnn.keras`, `artefactos_preprocesamiento.pkl`, `modelo_xgboost.pkl`), crean el entorno virtual, instalan dependencias, construyen `linea.db` si no existe y abren la app en `localhost:8000`. El sistema degrada con gracia: si ADRES no responde o Nemotron no tiene API key, la auditoría continúa con modelos locales.

---

## 4. 📊 Datos y Reproducibilidad

### P14. ¿Los datos son reales?
**Respuesta:** No. Son **datos sintéticos para fines académicos y de demostración** (Capstone SIC 2025). Los modelos y la metodología son aplicables a datos reales, pero para producción con datos reales se requieren los controles de Ley 1581 e ISO 27001 documentados. Está señalado explícitamente en ambos README y en la landing.

### P15. ¿Cómo reproducen sus resultados?
**Respuesta:** Ejecutar los notebooks en orden 01→08 con `requirements.txt`: 01 limpieza, 02 dataset maestro, 03 validación CUPS, 04 EDA, 05 modelos RF/XGB, 06 dashboard, 07 XGBoost avanzado (SHAP), 08 CNN. Las métricas consolidadas están en `documentacion/metricas_oficiales.md`, auditables desde `outputs/reports/metrics.json`. El CNN no es determinista en CPU: corridas limpias dieron 0.6727, 0.6984 y 0.7104.

### P16. ¿Cómo validaron los códigos CUPS?
**Respuesta:** Notebook 03 validó cada código contra el catálogo CUPS oficial. Hallazgo relevante: el código `890201-M` ("Terapia de rehidratación oral supervisada") **no cumple el formato CUPS de 6 dígitos pero se usa consistentemente** (52 usos HC, 58 prefactura) — es un código interno inventado que cualquier EPS glosaría. Quedó marcado `REQUIERE_REVISION` con Health & Life.

---

## 5. ⚖️ Cumplimiento Normativo y Seguridad

### P17. ¿Cómo cumplen la Ley 1581 de 2012?
**Respuesta:** Es el régimen colombiano de protección de datos personales. Documentamos: aviso de privacidad (`AVISO_PRIVACIDAD.md`), política de retención (`POLITICA_RETENCION.md`), análisis de riesgos (`ANALISIS_RIESGOS.md`) e inventario de activos (`INVENTARIO_ACTIVOS.csv`). Estado: **documentación lista, controles técnicos en progreso (Fase 1)** — y al usar datos sintéticos no hay datos personales reales en riesgo durante la demostración.

### P18. ¿Y la ISO/IEC 27001:2022?
**Respuesta:** Es el estándar de gestión de seguridad de la información. Definimos la política de seguridad (`POLITICA_SEGURIDAD.md`), el alcance del SGSI, el inventario de activos y el análisis de riesgos como **Fase 1 de implementación**. El documento `CUMPLIMIENTO_LEY1581_ISO27001.md` consolida el estado de ambos marcos.

### P19. ¿Qué pasa con la API key de Nemotron?
**Respuesta:** Nunca se versiona. Vive en `.env` (ignorado por git; existe `.env.example` como plantilla). El scraper de ADRES no requiere API key.

---

## 6. 🎯 Decisiones de Diseño y Proyección

### P20. ¿Qué fue lo más difícil del proyecto?
**Respuesta (sugerencia de enfoque):** La **auditoría honesta del CNN**. La referencia histórica (0.7487) no era reproducible; hicimos corridas limpias, documentamos la variabilidad (±0.02 en CPU), y reportamos la cifra reproducible (0.6727) en lugar de inflar el resultado. La integridad técnica por encima del número bonito — eso también responde por qué la documentación separa "fuente oficial" de "referencias históricas".

### P21. ¿Cómo escalaría esto a producción con datos reales?
**Respuesta:** Migrar SQLite a SQL Server/MySQL (`docs/MIGRATION.md`), implementar controles Ley 1581/ISO 27001 (encriptación, minimización, retención), conectar ADRES por servicio oficial en lugar de scraping, cachear inferencias, y monitorear drift del modelo con reentrenamiento periódico.

### P22. ¿Cuál sería el siguiente paso si continuaran?
**Respuesta (sugerencia):** (1) pipeline de reentrenamiento automático con datos reales anonimizados, (2) explicabilidad por caso más profunda (SHAP por cruce en la UI), (3) módulo de glosas post-factura (no solo pre), (4) integración con el sistema de facturación de la IPS.

---

## 💡 Tips para la sustentación

- Si preguntan por una métrica, **dirígelos a `documentacion/metricas_oficiales.md`** (fuente consolidada auditable).
- Si preguntan por el CNN y su bajo rendimiento: **reformularlo como decisión honesta de investigación** (P6), no como debilidad.
- Tener a mano: el diagrama del pipeline (`line_pipeline_arquitectura.svg`), el GIF de la demo (`line_demo.gif`) y la landing con el dashboard interactivo.
- Los datos son sintéticos: decirlo **antes** de que lo pregunten (P14).

---

*Documento de preparación interna — Equipo LINE, Capstone SIC 2025. Última actualización: 2026-08-02.*
