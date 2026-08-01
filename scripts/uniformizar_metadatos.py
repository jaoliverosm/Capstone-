# -*- coding: utf-8 -*-
"""
uniformizar_metadatos.py
========================
Uniforma la metadadata de los documentos Office del proyecto LINE/Capstone:

  * Autor / lastModifiedBy  -> "Jefersson Aldair Oliveros Monroy"
  * Fechas de creación      -> semana actual (2026-07-31)
  * Título / asunto / descripción / palabras clave -> no vacíos

Corrige además el caso del guion (no tenia docProps/core.xml en absoluto:
se crea el part, se registra en [Content_Types].xml y _rels/.rels).

Uso:  python uniformizar_metadatos.py
"""
import os
import re
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent  # Capstone/

AUTOR = "Jefersson Aldair Oliveros Monroy"
CREATED = "2026-07-31T10:00:00Z"
MODIFIED = "2026-07-31T11:00:00Z"

CT_CORE = "application/vnd.openxmlformats-package.core-properties+xml"
CT_APP = "application/vnd.openxmlformats-officedocument.extended-properties+xml"
REL_CORE = "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties"
REL_APP = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties"

APP_XML_DEFAULT = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
    'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
    '<Application>Microsoft Office</Application><DocSecurity>0</DocSecurity>'
    '<ScaleCrop>false</ScaleCrop><Company>Equipo SICortex</Company>'
    '<LinksUpToDate>false</LinksUpToDate><SharedDoc>false</SharedDoc>'
    '<HyperlinksChanged>false</HyperlinksChanged><AppVersion>16.0000</AppVersion>'
    '</Properties>'
)


def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def core_xml(title, subject, description, keywords, created, modified) -> str:
    """Genera docProps/core.xml completo y limpio."""
    parts = []
    if title:
        parts.append(f"<dc:title>{_esc(title)}</dc:title>")
    if subject:
        parts.append(f"<dc:subject>{_esc(subject)}</dc:subject>")
    parts.append(f"<dc:creator>{_esc(AUTOR)}</dc:creator>")
    if keywords:
        parts.append(f"<cp:keywords>{_esc(keywords)}</cp:keywords>")
    if description:
        parts.append(f"<cp:description>{_esc(description)}</cp:description>")
    parts.append(f"<cp:lastModifiedBy>{_esc(AUTOR)}</cp:lastModifiedBy>")
    parts.append("<cp:revision>2</cp:revision>")
    parts.append(f'<dcterms:created xsi:type="dcterms:W3CDTF">{created}</dcterms:created>')
    parts.append(f'<dcterms:modified xsi:type="dcterms:W3CDTF">{modified}</dcterms:modified>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        + "".join(parts) + "</cp:coreProperties>"
    )


def _read_entries(path: Path) -> dict:
    with zipfile.ZipFile(path) as z:
        return {i.filename: (i, z.read(i.filename)) for i in z.infolist()}


def _write_entries(path: Path, entries: dict) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, (info, data) in entries.items():
            zout.writestr(info, data)
    os.replace(tmp, path)


def aplicar(path: Path, meta: dict) -> str:
    """Aplica metadatos a un docx/pptx; crea docProps si faltan."""
    entries = _read_entries(path)
    has_core = "docProps/core.xml" in entries

    core = core_xml(
        meta.get("title", ""), meta.get("subject", ""),
        meta.get("description", ""), meta.get("keywords", ""),
        meta.get("created", CREATED), meta.get("modified", MODIFIED),
    )

    if has_core:
        entries["docProps/core.xml"] = (entries["docProps/core.xml"][0], core.encode("utf-8"))
        if "docProps/app.xml" in entries and meta.get("app") is not None:
            entries["docProps/app.xml"] = (entries["docProps/app.xml"][0], meta["app"].encode("utf-8"))
        estado = "actualizado"
    else:
        # Crear docProps/core.xml + app.xml
        core_item = zipfile.ZipInfo("docProps/core.xml", (2026, 7, 31, 10, 0, 0))
        core_item.compress_type = zipfile.ZIP_DEFLATED
        entries["docProps/core.xml"] = (core_item, core.encode("utf-8"))

        app = meta.get("app") or APP_XML_DEFAULT
        app_item = zipfile.ZipInfo("docProps/app.xml", (2026, 7, 31, 10, 0, 0))
        app_item.compress_type = zipfile.ZIP_DEFLATED
        entries["docProps/app.xml"] = (app_item, app.encode("utf-8"))

        # Registrar en [Content_Types].xml
        ct = entries["[Content_Types].xml"][1].decode("utf-8")
        if "docProps/core.xml" not in ct:
            extra = (f'<Override PartName="/docProps/core.xml" ContentType="{CT_CORE}"/>'
                     f'<Override PartName="/docProps/app.xml" ContentType="{CT_APP}"/>')
            ct = ct.replace("</Types>", extra + "</Types>")
        entries["[Content_Types].xml"] = (entries["[Content_Types].xml"][0], ct.encode("utf-8"))

        # Registrar en _rels/.rels
        rels = entries["_rels/.rels"][1].decode("utf-8")
        if "core.xml" not in rels:
            extra = (f'<Relationship Id="rId901" Type="{REL_CORE}" Target="docProps/core.xml"/>'
                     f'<Relationship Id="rId902" Type="{REL_APP}" Target="docProps/app.xml"/>')
            rels = rels.replace("</Relationships>", extra + "</Relationships>")
        entries["_rels/.rels"] = (entries["_rels/.rels"][0], rels.encode("utf-8"))
        estado = "creado (no tenia docProps)"

    _write_entries(path, entries)
    return estado


ARCHIVOS = {
    "Documento_Enlaces_Entrega.docx": {
        "title": "LINE — Documento de Enlaces y Recursos",
        "subject": "Entrega en plataforma — Samsung Innovation Campus 2025",
        "description": ("Documento complementario al informe técnico (Archivo 1) que reúne todos los "
                        "enlaces del proyecto LINE — Auditor Médico Digital: repositorios, landing, "
                        "documentación y video."),
        "keywords": "LINE, enlaces, entrega, capstone, Health & Life",
        "created": CREATED, "modified": MODIFIED,
    },
    "Informe_Tecnico_LINE_APA.docx": {
        "title": "LINE: Auditor Médico Digital — Informe Técnico",
        "subject": "Capstone — Sistemas Inteligentes y Computacionales",
        "description": ("Informe técnico del proyecto LINE — Auditor Médico Digital: detección predictiva "
                        "de inconsistencias en prefacturación mediante inteligencia artificial "
                        "(Samsung Innovation Campus 2025 · Reto Health & Life IPS SAS)."),
        "keywords": "LINE, auditoría médica, IA, XGBoost, CNN, prefacturación",
    },
    "Guion para video capstone .docx": {
        "title": "Guion para video capstone — LINE",
        "subject": "Video pitch (máximo 3 minutos)",
        "description": ("Guion del video de presentación del proyecto LINE — Auditor Médico Digital "
                        "(equipo SICortex)."),
        "keywords": "LINE, video, pitch, capstone",
        "created": CREATED, "modified": MODIFIED,
    },
    "LINE-Auditor-Medico-Digital.pptx": {
        "title": "LINE — Auditor Médico Digital (Presentación)",
        "subject": "Presentación del proyecto",
        "description": ("Presentación del proyecto LINE — Auditor Médico Digital "
                        "(Samsung Innovation Campus 2025 · Reto Health & Life IPS SAS)."),
        "keywords": "LINE, presentación, capstone, IA",
        "created": CREATED, "modified": MODIFIED,
    },
}


def main() -> int:
    carpeta = RAIZ / "documentacion"
    for nombre, meta in ARCHIVOS.items():
        ruta = carpeta / nombre
        if not ruta.exists():
            print(f"!! {nombre}: NO EXISTE")
            continue
        estado = aplicar(ruta, meta)
        print(f"OK {nombre}: {estado}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
