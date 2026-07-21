# Hallazgos EDA — dataset maestro

1. **Fugas (sin prefactura):** 152 procedimientos con soporte clínico sin facturar. Pérdida estimada: $41,571,660 COP (valor unitario promedio $273,498).

2. **Temporal:** tasa mensual estable entre 13.5% y 25.1% — sin estacionalidad fuerte; errores a ritmo constante.

3. **Cantidades:** el 46% de los inconsistentes tiene diferencia de cantidad != 0.

4. **Flags de cruce:** casi deterministas — sin_prefactura (fuga): 100%, sin_soporte_hc: 100%, codigo_no_coincide: 100%, cantidad_diferente: 100%. El target fue generado por reglas cuyos insumos están en estas features; el valor del modelo es priorizar por probabilidad y generalizar, no redescubrir las reglas.
