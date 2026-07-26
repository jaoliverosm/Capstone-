# Hallazgos EDA — dataset maestro

1. **Target:** 2,477 consistentes (79.2%) vs 649 inconsistentes (20.8%). Alerta dominante: SIN_SOPORTE_CLINICO (157 casos).

2. **Dimensiones:** tasa homogénea entre EPS (18.4%–23.3%) y sedes (18.7%–22.7%): problema transversal/sistémico.

3. **Fugas (sin prefactura):** 152 procedimientos con soporte clínico sin facturar. Pérdida estimada: $78,046,000 COP valorando cada fuga con el precio de referencia de su CUPS × cantidad realizada (0 sin precio de referencia, valoradas al promedio). Estimación conservadora con promedio simple de ítems facturados ($287,476): $43,696,371.

4. **Temporal:** tasa mensual estable entre 13.5% y 25.1% — sin estacionalidad fuerte; errores a ritmo constante.

5. **Cantidades:** el 46% de los inconsistentes tiene diferencia de cantidad != 0.

6. **Flags de cruce:** casi deterministas — sin_prefactura (fuga): 100%, sin_soporte_hc: 100%, codigo_no_coincide: 100%, cantidad_diferente: 100%. El target fue generado por reglas cuyos insumos están en estas features; el valor del modelo es priorizar por probabilidad y generalizar, no redescubrir las reglas.
