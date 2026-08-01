# -*- coding: utf-8 -*-
"""
actualizar_informe_cifras.py
============================
Inserta las cifras oficiales de fuga de ingresos en el Informe Técnico LINE (APA):
  * Contexto del problema: 152 procedimientos sin facturar / $78,046,000 COP
  * Impacto económico estimado: cuantificación sobre el dataset (3,126 cruces,
    649 inconsistentes = 20.8 %, 152 fugas).

Fuente de las cifras: Capstone/outputs/reports/eda_hallazgos.md (fuente oficial).
Preserva el estilo (deep-copy del párrafo vecino, incluida numeración de viñetas).
Escribe primero a un temporal y lo intercambia por el original al validar.
"""
import copy
import sys

from docx import Document

DOCX = r"Capstone/documentacion/Informe_Tecnico_LINE_APA.docx"
TMP = DOCX.replace(".docx", "_tmp.docx")

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

BULLET_FUGAS = "Fugas de ingresos: procedimientos realizados y registrados en HC que no aparecen en la prefactura."

NUEVA_VIÑETA_FUGAS = (
    "Fugas de ingresos: procedimientos realizados y registrados en HC que no aparecen en la prefactura. "
    "En la base analizada (3,126 cruces) se identificaron 152 procedimientos con soporte clínico sin facturar, "
    "con una pérdida estimada de $78,046,000 COP (valoración con el precio de referencia de cada CUPS "
    "multiplicado por la cantidad realizada)."
)

CUERPO_IMPACTO_ANTERIOR = "La implementación del sistema permitirá reducir las glosas"

PARRAFO_IMPACTO_NUEVO = (
    "Sobre el conjunto de datos analizado (3,126 cruces, 649 inconsistentes, 20.8 %), la aplicación detectó "
    "152 procedimientos con soporte clínico sin facturar, cuya pérdida estimada asciende a $78,046,000 COP "
    "(precio de referencia por CUPS × cantidad realizada). La detección temprana de estas fugas antes del "
    "envío a cobro permite a Health & Life IPS SAS recuperar ingresos que actualmente se pierden en la "
    "auditoría retrospectiva."
)


def _set_para_text(p_el, text: str) -> None:
    """Deja un solo run con el texto dado (conserva pPr y primer rPr del original)."""
    runs = p_el.findall(W + "r")
    for r in runs[1:]:
        p_el.remove(r)
    if runs:
        ts = runs[0].findall(W + "t")
        for t in ts[1:]:
            runs[0].remove(t)
        if ts:
            ts[0].text = text
        else:
            t = p_el.makeelement(W + "t", {})
            t.text = text
            runs[0].append(t)
    else:
        r = p_el.makeelement(W + "r", {})
        t = p_el.makeelement(W + "t", {})
        t.text = text
        r.append(t)
        p_el.append(r)


def insertar_parrafo_tras(ancla, texto: str):
    """Inserta un párrafo nuevo (copiando estilo del ancla) inmediatamente después."""
    nuevo = copy.deepcopy(ancla._p)
    _set_para_text(nuevo, texto)
    ancla._p.addnext(nuevo)
    return nuevo


def main() -> int:
    doc = Document(DOCX)
    hit_bullet = hit_impacto = False

    for p in doc.paragraphs:
        t = p.text.strip()
        if t == BULLET_FUGAS:
            _set_para_text(p._p, NUEVA_VIÑETA_FUGAS)
            hit_bullet = True
        elif t.startswith(CUERPO_IMPACTO_ANTERIOR):
            insertar_parrafo_tras(p, PARRAFO_IMPACTO_NUEVO)
            hit_impacto = True

    if not hit_bullet:
        print("ERROR: no se encontró la viñeta 'Fugas de ingresos...'")
        return 2
    if not hit_impacto:
        print("ERROR: no se encontró el párrafo de Impacto económico estimado")
        return 3

    doc.save(TMP)
    print("Temporal OK:", TMP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
