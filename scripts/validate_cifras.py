# -*- coding: utf-8 -*-
"""
validate_cifras.py
==================
Validador de consistencia de cifras del proyecto LINE.

Cruza las cifras oficiales (fuente: `outputs/reports/eda_hallazgos.md` y
`documentacion/metricas_oficiales.md`) contra su aparición en:
  1. Capstone/documentacion/LANDING_LINE.html   (página pública)
  2. Capstone/README.md                          (readme del repo)
  3. Capstone/documentacion/Informe_Tecnico_LINE_APA.docx  (Archivo 1 de la entrega)

Niveles:
  * critica     — debe aparecer en las 3 fuentes (son las cifras de la entrega).
  * advertencia — se reporta si falta, pero no rompe el exit code (p. ej., cifras
                  que solo viven en metricas_oficiales, como la matriz de confusión).

Uso:
    python validate_cifras.py            # valida y sale con 0/1
    python validate_cifras.py --json     # salida JSON (para CI)

Exit: 0 = sin fallas críticas, 1 = hay cifras críticas ausentes.
"""
import argparse
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

# Capstone/  (scripts/validate_cifras.py -> subir un nivel)
RAIZ = Path(__file__).resolve().parent.parent

RUTAS = {
    "landing": RAIZ / "documentacion" / "LANDING_LINE.html",
    "readme": RAIZ / "README.md",
    "informe": RAIZ / "documentacion" / "Informe_Tecnico_LINE_APA.docx",
}

# (nombre, patrón, nivel)
# Fuente: eda_hallazgos.md + metricas_oficiales.md (corrida limpia 29-jul-2026).
CIFRAS = [
    ("3,126 cruces",             r"(?<![0-9.,])3\s?[.,]?\s?126(?!\d)", "critica"),
    ("2,477 consistentes",       r"(?<![0-9.,])2\s?[.,]?\s?477(?!\d)", "critica"),
    ("649 inconsistentes",       r"(?<![0-9.,])649(?!\d)",       "critica"),
    ("20.8% inconsistencia",     r"20[.,]8\s?%",                 "critica"),
    ("152 procedimientos fuga",  r"(?<![0-9.,])152(?!\d)",       "critica"),
    ("$78,046,000 COP",          r"\$\s?78[.,]046[.,]000",       "critica"),
    ("AUC XGBoost 0.8983",       r"0[.,]898",                    "critica"),
    ("Precisión 99.2%",          r"99[.,]2\s?%",                 "critica"),
    ("F1 0.7864",                r"0[.,]786",                    "critica"),
    ("AUC RF 0.9185",            r"0[.,]91[0-9]",                "critica"),
    ("CNN AUC 0.6727",           r"0[.,]67[0-9]",                "advertencia"),
    ("Matriz TN=742 FP=1",       r"(?<![0-9.,])742(?!\d)",       "advertencia"),
]

# Abreviatura oficial de $78,046,000 usada en landing/guion
ALIAS_78M = r"\$\s?78\s?M"


class _ExtractorHTML(HTMLParser):
    """Extrae texto visible + contenido srcdoc (workflow embebido), sin tags.

    Ignora <script>/<style> (el CSS/JS de la landing no debe contar como
    contenido visible). Convierte entidades (&lt;td&gt; -> <td>). El srcdoc se
    parsea recursivamente para que su <style>/<script> interno no contamine.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.partes: list[str] = []
        self._ignorar = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._ignorar += 1
        if self._ignorar == 0:
            for k, v in attrs:
                if v and k.lower() == "srcdoc":
                    sub = _ExtractorHTML()
                    sub.feed(html.unescape(v))
                    self.partes.append(sub.texto())

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._ignorar > 0:
            self._ignorar -= 1

    def handle_data(self, dato):
        if self._ignorar == 0:
            self.partes.append(dato)

    def texto(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self.partes))


def _normalizar(texto: str) -> str:
    """Colapsa espacios. El stripping de tags ocurre en `_contenido`:
    HTML via _ExtractorHTML (regex sobre tags se tragaria el srcdoc ~200KB),
    docx via re.sub sobre el XML antes de llamar aqui.
    """
    t = re.sub(r"\s+", " ", texto)
    return t


def _contenido(ruta: Path) -> str:
    """Lee el contenido de landing/readme/docx."""
    if not ruta.exists():
        return ""
    if ruta.suffix == ".html":
        parser = _ExtractorHTML()
        parser.feed(ruta.read_text(encoding="utf-8", errors="replace"))
        return parser.texto()
    if ruta.suffix == ".docx":
        import zipfile
        z = zipfile.ZipFile(ruta)
        xml = z.read("word/document.xml").decode("utf-8", "replace")
        # Quitar tags XML antes de normalizar: si no, atributos como
        # w:after="152" generan falsos positivos en los patrones de dígitos
        return _normalizar(re.sub(r"<[^>]+>", " ", xml))
    return _normalizar(ruta.read_text(encoding="utf-8", errors="replace"))


def _buscar(texto: str, patron: str) -> bool:
    return re.search(patron, texto, re.IGNORECASE) is not None


def validar() -> dict:
    contenidos = {k: _contenido(v) for k, v in RUTAS.items()}
    resultados = {}

    for nombre, patron, nivel in CIFRAS:
        fila = {}
        for fuente, texto in contenidos.items():
            ok = _buscar(texto, patron)
            # El $78,046,000 puede aparecer abreviado como $78M
            if not ok and patron.startswith(r"\$\s?78"):
                ok = _buscar(texto, ALIAS_78M)
            fila[fuente] = bool(ok)
        resultados[nombre] = {"fuentes": fila, "nivel": nivel}

    return {"cifras": resultados, "archivos": list(RUTAS.keys())}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    datos = validar()
    criticas_faltan = {
        k: v for k, v in datos["cifras"].items()
        if v["nivel"] == "critica" and not all(v["fuentes"].values())
    }
    advertencias = {
        k: v for k, v in datos["cifras"].items()
        if v["nivel"] == "advertencia" and not all(v["fuentes"].values())
    }

    if args.json:
        print(json.dumps(datos, ensure_ascii=False, indent=2))
    else:
        print("=" * 64)
        print("VALIDACIÓN DE CIFRAS — LINE Auditor Médico Digital")
        print("=" * 64)
        for nombre, v in datos["cifras"].items():
            marca = "OK " if all(v["fuentes"].values()) else ("!! " if v["nivel"] == "critica" else "-- ")
            detalle = " | ".join(
                f"{f}:{'✓' if ok else '✗'}" for f, ok in v["fuentes"].items()
            )
            print(f"{marca} {nombre:<28} {detalle}")
        print("=" * 64)
        if criticas_faltan:
            print(f"FALLAS CRÍTICAS: {len(criticas_faltan)} cifra(s) ausente(s).")
            return 1
        if advertencias:
            print(f"Advertencias (no bloqueantes): {len(advertencias)} — revisar informe.")
        print("TODO CONSISTENTE ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
