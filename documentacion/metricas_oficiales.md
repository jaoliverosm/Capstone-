# Métricas Oficiales — LINE Auditor Médico Digital

> Generado desde `outputs/reports/metrics.json` (corrida limpia, 29-jul-2026)
> Dataset: 3,126 registros (2,477 consistentes / 649 inconsistentes)
> Split: 70/30 estratificado

---

## 1. Escenario A: Producción (18 features originales)

### Random Forest

| Métrica | CV 5-fold (media ± std) | Test (th=0.50) | Test (th recall~85%) |
|---------|------------------------|-----------------|---------------------|
| AUC-ROC | 0.8884 ± 0.0157 | **0.9185** | — |
| Precisión | 0.9363 ± 0.0168 | 0.9225 | 0.6014 |
| Recall | 0.5792 ± 0.0441 | 0.6103 | **0.8513** |
| F1 | 0.7147 ± 0.0333 | 0.7346 | 0.7049 |
| Accuracy | — | 0.9083 | 0.8518 |

### XGBoost ⭐ (Modelo en producción)

> ⚠️ **Nota importante:** Las columnas "Test (th=0.50)" y "Test (th recall~85%)" corresponden al pipeline XGBoost básico entrenado en el **notebook 05** (`05_modelos_rf_xgb.ipynb`). La columna "Producción (th=0.896)" corresponde al XGBoost avanzado con optimización de hiperparámetros del **notebook 07** (`07_entrenamiento_xgboost_avanzado.ipynb`). Son **pipelines de entrenamiento diferentes**, no el mismo modelo con distinto threshold. El AUC-ROC 0.9129 (notebook 05) y el AUC-ROC 0.8983 (notebook 07) no son comparables directamente porque usan distintos hiperparámetros (GridSearchCV en 07 vs defaults en 05) y distinta optimización de threshold.

| Métrica | CV 5-fold (media ± std) | Test (th=0.50) | Test (th recall~85%) | Producción (th=0.896) |
|---------|------------------------|-----------------|---------------------|----------------------|
| AUC-ROC | 0.8802 ± 0.0090 | **0.9129** | — | **0.8983** |
| Precisión | 0.8270 ± 0.0186 | 0.8068 | 0.5866 | **0.9922** |
| Recall | 0.7004 ± 0.0300 | 0.7282 | **0.8513** | 0.6513 |
| F1 | 0.7578 ± 0.0129 | 0.7655 | 0.6946 | **0.7864** |
| Accuracy | — | 0.9072 | 0.8443 | 0.9264 |
| Threshold | — | 0.50 | 0.0822 | **0.896** |

**Matriz de confusión (th=0.896):** TN=742, FP=1, FN=68, TP=127

---

## 2. Escenario B: Features CNN (features derivadas del pipeline CNN)

### Random Forest + CNN features

| Métrica | CV 5-fold (media ± std) | Test (th=0.50) | Test (th recall~85%) |
|---------|------------------------|-----------------|---------------------|
| AUC-ROC | 0.8371 ± 0.0179 | **0.8500** | — |
| Precisión | 0.9583 ± 0.0174 | 0.9368 | 0.3458 |
| Recall | 0.4581 ± 0.0189 | 0.4564 | **0.8513** |
| F1 | 0.6198 ± 0.0202 | 0.6138 | 0.4919 |

### XGBoost + CNN features

| Métrica | CV 5-fold (media ± std) | Test (th=0.50) | Test (th recall~85%) |
|---------|------------------------|-----------------|---------------------|
| AUC-ROC | 0.8404 ± 0.0145 | **0.8707** | — |
| Precisión | 0.7571 ± 0.0249 | 0.7595 | 0.3943 |
| Recall | 0.6124 ± 0.0237 | 0.6154 | **0.8513** |
| F1 | 0.6762 ± 0.0053 | 0.6799 | 0.5390 |

---

## 3. CNN MobileNetV2 (Referencia)

> Pipeline tabular → imagen 32×32×3. No determinista en CPU.

| Métrica | Valor |
|---------|-------|
| **AUC-ROC (consolidado)** | **0.6727** |
| Variabilidad (3 corridas limpias) | 0.6727 / 0.6984 / 0.7104 |
| Rango recomendado | **~0.67 – 0.70** |
| Threshold óptimo | 0.4273 |
| Accuracy (th óptimo) | 0.6800 |
| Precisión (th óptimo) | 0.3427 |
| Recall (th óptimo) | 0.5641 |
| F1 (th óptimo) | 0.4264 |
| Accuracy (th=0.50) | 0.8081 |
| Precisión (th=0.50) | 0.7586 |
| Recall (th=0.50) | 0.1128 |

> **Cifra histórica (obsoleta):** 0.7487 — no reproducible con el notebook actual.

---

## 4. Resumen Comparativo — Modelos en Producción

> ⚠️ **Nota:** RF y XGBoost (th=0.50) provienen del **notebook 05**. XGBoost (th=0.896, AUC 0.8983) proviene del **notebook 07**. No comparar directamente entre notebooks (ver nota en Sección 1).

| Modelo | AUC-ROC | Precisión | Recall | F1 | Threshold | Notebook |
|--------|---------|-----------|--------|----|-----------|----------|
| **XGBoost ⭐** | **0.8983** | **0.9922** | 0.6513 | **0.7864** | 0.896 | 07 |
| Random Forest | 0.9185 | 0.9225 | 0.6103 | 0.7346 | 0.50 | 05 |
| CNN MobileNetV2 | 0.6727 | 0.3427 | 0.5641 | 0.4264 | 0.4273 | 08 |

---

## 5. Features más importantes (XGBoost producción)

| # | Feature | Gain (importancia) | SHAP |
|---|---------|-------------------|------|
| 1 | `coincide_codigo_cups` | 0.6566 | 1.6765 |
| 2 | `diferencia_cantidad` | 0.2037 | 0.4018 |
| 3 | `ratio_cantidad` | 0.0153 | — |
| 4 | `eps_atencion` | 0.0121 | — |
| 5 | `dias_diferencia` | 0.0121 | 0.4526 |
| 6 | `edad` | 0.0117 | 0.8730 |
| 7 | `diag_encoded` | 0.0114 | 0.5404 |

---

*Documento generado el 30-jul-2026. Fuente: `Capstone/outputs/reports/metrics.json`*
