# Guía de Implementación: Cumplimiento Ley 1581/2012 e ISO/IEC 27001:2022
## Proyecto: Auditor Médico Digital (Capstone)

**Fecha:** 30 de julio de 2026  
**Versión:** 1.0  
**Estado:** Borrador para revisión  
**Autor:** Jefersson Aldair Oliveros Monroy (líder del proyecto)  

---

## Resumen ejecutivo

| Normativa | Estado Actual | Acción Requerida |
|-----------|---------------|------------------|
| **Ley 1581/2012** (Protección datos personales Colombia) | No cumple para producción | Implementar 10 controles mínimos viables |
| **ISO/IEC 27001:2022** (SGSI) | No certificable (~5% controles) | Definir hoja de ruta 6-12 meses |

> **Nota clave:** El proyecto usa **datos sintéticos** para fines académicos (entrega 04-ago-2026). **No viola la ley hoy**. Pero el sistema **diseñado para producción SÍ requiere** estos controles antes de procesar datos reales de pacientes.

---

## Objetivos de este documento

1. **Consolidar** hallazgos de cumplimiento legal y de seguridad
2. **Priorizar** acciones por impacto/riesgo
3. **Dejar trazabilidad** para revisión futura (post-entrega, piloto, producción)
4. **Servir de base** para anexos en informe técnico y presentación

---

## 1. LEY 1581 DE 2012 — Checklist de Cumplimiento

### 1.1 Clasificación de datos del proyecto

| Dato | Categoría Ley 1581 | Nivel | Artículos clave |
|------|-------------------|-------|-----------------|
| Historias clínicas, diagnósticos CIE-10, procedimientos CUPS | **Sensibles (salud)** | Máximo | Art. 5, 6, 7 |
| Nombres, cédulas, teléfonos, emails, EPS, sede | **Privados** | Alto | Art. 5, 10, 11 |
| Datos financieros/facturación | **Semiprivados** | Medio-Alto | Art. 5, 10 |

### 1.2 Controles obligatorios — Estado actual

| # | Control | Estado | Brecha | Prioridad |
|---|---------|--------|--------|-----------|
| 1 | Aviso de privacidad público | No | No existe | Crítica |
| 2 | Mecanismo consentimiento expreso, granular, revocable | No | No implementado | Crítica |
| 3 | Política interna protección de datos | No | No documentada | Crítica |
| 4 | Registro Nacional Bases Datos (RNBD - SIC) | No | Trámite no iniciado | Crítica |
| 5 | Procedimiento derechos ARCO (15 días hábiles) | No | No hay portal/API/proceso | Crítica |
| 6 | Cifrado AES-256 (reposo) + TLS 1.3 (tránsito) | No | No verificado | Crítica |
| 7 | Análisis de Impacto (PIA) para datos salud | No | Requerido por Guía SIC | Alta |
| 8 | Contratos de encargo con proveedores (Nemotron, cloud) | No | Sin cláusulas seguridad | Alta |
| 9 | Política retención/supresión (ej. 5 años datos salud) | No | No definida | Alta |
| 10 | DPO designado (interno/externo) | No | No asignado | Alta |

### 1.3 Sanciones por incumplimiento (SIC)

| Incumplimiento | Sanción máxima |
|----------------|----------------|
| Tratar datos salud sin autorización expresa | **2.000 SMMLV** (~$2.600M COP 2026) + cierre BD |
| No registrar en RNBD | Multa + suspensión tratamiento |
| Sin aviso de privacidad | Multa + medida correctiva |
| Fuga datos médicos (sin seguridad) | Multa agravada + posible responsabilidad penal |

---

## 2. ISO/IEC 27001:2022 — Análisis de Brechas

### 2.1 Cláusulas 4-10 (SGC obligatorio) — 0/7 implementadas

| Cláusula | Requisito | Estado | Acción |
|----------|-----------|--------|--------|
| **4. Contexto** | Partes interesadas, alcance SGSI, requisitos legales | No | Definir alcance + mapear Ley 1581 |
| **5. Liderazgo** | Política seguridad firmada, roles (DPO/CISO) | No | Redactar política 1-página, firmar líder |
| **6. Planificación** | **Análisis de riesgos** (activos, amenazas, impacto), Plan tratamiento, Objetivos medibles | No | Núcleo de ISO 27001 — hacer ISO 27005 ligero |
| **7. Soporte** | Recursos, competencia, conciencia, info documentada | No | Inventario políticas/procedimientos |
| **8. Operación** | Implementar controles Anexo A, gestionar riesgos residuales, continuidad | Parcial | Priorizar controles tecnológicos |
| **9. Evaluación** | Auditorías internas, revisión dirección, KPIs seguridad | No | Definir métricas + calendarizar auditoría |
| **10. Mejora** | No conformidades, acciones correctivas, mejora continua | No | Establecer proceso PDCA |

### 2.2 Anexo A — Controles críticos para este proyecto (top 20 de 93)

| Control | Nombre | Estado | Acción inmediata |
|---------|--------|--------|------------------|
| **A.5.1** | Políticas de seguridad | No | Redactar política 1-página |
| **A.5.9** | Inventario de activos | No | CMDB: datos, modelos, código, infra, APIs |
| **A.5.11** | Clasificación información | Parcial | Formalizar política + etiquetado automático |
| **A.5.19** | Seguridad en desarrollo | Parcial | SAST (Bandit/Semgrep) + secrets scanning |
| **A.5.31** | Marco legal/regulatorio | Parcial | Mapear Ley 1581 Art. x Control ISO |
| **A.5.34** | Privacidad / PII | No | Integrar con controles Ley 1581 |
| **A.8.2** | Gestión privilegios | No | Least privilege en Jupyter, API, BD |
| **A.8.3** | Restricción acceso info | No | RBAC en `data/`, `outputs/models/`, API |
| **A.8.4** | Acceso código fuente | Parcial | Branch protection + CODEOWNERS + signed commits |
| **A.8.5** | Autenticación segura | No | MFA + JWT en API (`server.py`) |
| **A.8.9** | Gestión secretos | **Crítica** | Vault/Keyring — **NO .env en repo** |
| **A.8.15** | Logging/registro eventos | No | Logs estructurados + retención 1 año + alertas |
| **A.8.21** | Seguridad servicios red | No | WAF, rate limiting, validación input en API |
| **A.8.24** | Criptografía | No | Política claves, certificados, TLS 1.3 |
| **A.8.25** | Desarrollo seguro | Parcial | SAST en CI/CD, threat modeling |
| **A.8.30** | APIs seguras | No | Auth, validación, rate limit, versionado en `server.py` |
| **A.8.31** | Gestión vulnerabilidades | No | `pip-audit` + Dependabot + SBOM (Syft) |
| **A.7.1** | Perímetros físicos | No | Control acceso laptops/servidor local |
| **A.6.3** | Concienciación seguridad | No | Capacitación equipo (phishing, manejo datos) |
| **A.5.24** | Plan respuesta incidentes | No | Definir CSIRT, playbooks, comunicación SIC |

---

## 3. PLAN DE ACCIÓN PRIORIZADO

### Fase 1 — Crítica (Antes de cualquier piloto con datos reales)
*Tiempo estimado: 2-4 semanas*

| # | Acción | Control ISO | Control Ley 1581 | Responsable | Evidencia |
|---|--------|-------------|------------------|-------------|-----------|
| 1 | **Rotar y guardar secretos en vault** (API keys, tokens Nemotron, BD) | A.8.9 | Seguridad | Líder técnico | Vault configurado, 0 secretos en código/.env |
| 2 | **Cifrar `data/raw/` en reposo + TLS 1.3 en API** | A.8.24, A.8.21 | Seguridad, Confidencialidad | DevOps/Backend | Certificados válidos, BD cifrada |
| 3 | **Autenticación + RBAC en `server.py`** (JWT, roles: auditor, admin, read-only) | A.8.2, A.8.3, A.8.5 | Acceso restringido | Backend | API protegida, logs de acceso |
| 4 | **`pip-audit` + Dependabot + SBOM (Syft) en CI** | A.8.31, A.5.17 | Seguridad cadena suministro | DevOps | Pipeline con gate de seguridad |
| 5 | **Branch protection + CODEOWNERS + signed commits en GitHub** | A.8.4 | Integridad código | Líder técnico | Reglas aplicadas en repo |

### Fase 2 — Alta (Primer mes de piloto)
*Tiempo estimado: 4-6 semanas*

| # | Acción | Control ISO | Control Ley 1581 | Responsable | Evidencia |
|---|--------|-------------|------------------|-------------|-----------|
| 6 | **Logging estructurado + retención 1 año + alertas básicas** (fallos auth, accesos anómalos, errores 5xx) | A.8.15, A.5.22 | Registros, Seguridad | Backend/DevOps | Logs en SIEM/local, alertas Telegram/email |
| 7 | **Política de Seguridad de la Información (1 página, firmada por líder)** | Cl. 5, A.5.1 | Liderazgo, Responsabilidad | Líder proyecto | PDF firmado en `documentacion/POLITICA_SEGURIDAD.md` |
| 8 | **Inventario de activos (CMDB ligera)** — datos, modelos, código, infra, APIs, proveedores | A.5.9 | Inventario bases datos | Líder técnico | `documentacion/INVENTARIO_ACTIVOS.csv` |
| 9 | **Análisis de riesgos ISO 27005 simplificado** (10 activos principales) | Cl. 6.1.2 | Planificación | Líder + equipo | `documentacion/ANALISIS_RIESGOS.md` |
| 10 | **Aviso de privacidad público + mecanismo consentimiento** | - | Art. 10, 15, 16 | Legal/Líder | Web/app con aviso, checkbox consentimiento |

### Fase 3 — Media (Antes de producción)
*Tiempo estimado: 2-3 meses*

| # | Acción | Control ISO | Control Ley 1581 | Responsable | Evidencia |
|---|--------|-------------|------------------|-------------|-----------|
| 11 | **Análisis de Impacto (PIA) para datos salud** (Guía SIC) | A.5.34 | Art. 6, 7 | Legal/DPO | Informe PIA firmado |
| 12 | **Registro en RNBD (SIC)** | - | Art. 25 | Legal/DPO | Certificado registro SIC |
| 13 | **Procedimiento ARCO** (portal/API + SLA 15 días) | - | Art. 14, 15 | Backend/Legal | Endpoint `/arco` documentado |
| 14 | **Contratos de encargo con proveedores** (Nemotron, hosting, GitHub) | A.5.16, A.5.17 | Encargados tratamiento | Legal | DPAs firmados |
| 15 | **Política retención/supresión** (datos crudos 5 años, logs 2 años, modelos versionados) | A.8.10, A.8.13 | Supresión | Legal/DevOps | Documento + jobs automáticos |
| 16 | **DPO designado** (interno/externo) con reporte a gerencia | A.5.2 | Art. 17 | Gerencia | Acta designación |
| 17 | **Plan continuidad negocio + respaldos probados** | A.5.30, A.8.13, A.8.14 | Disponibilidad | DevOps | BIA + test restore mensual |

---

## 4. PARA LA ENTREGA ACADÉMICA (04-AGO-2026)

### 4.1 Qué incluir en el informe técnico / presentación

| Sección | Contenido | Valor académico |
|---------|-----------|-----------------|
| **4.7 Consideraciones legales y de seguridad** | Tabla mapeando Ley 1581 Art. → Controles ISO 27001 → Estado actual → Hoja de ruta | Muestra madurez profesional, visión de ciclo de vida |
| **Anexo A: Análisis de riesgos simplificado** | 10 activos, amenazas (fuga, envenenamiento modelo, DoS, insider), valoración cualitativa (Alto/Medio/Bajo) | Núcleo de ISO 27001 Cl. 6 |
| **Anexo B: Plan de tratamiento de riesgos** | Controles seleccionados (A.8.9, A.8.25, A.8.30, A.5.11, A.5.19), responsable, fecha objetivo | Demuestra aplicabilidad real |
| **Anexo C: Hoja de ruta certificación** | Fases: 1) Políticas + inventario, 2) Controles técnicos, 3) Auditoría interna, 4) Certificación | Visión de negocio, escalabilidad |
| **Disclaimer explícito en README** | *"Datos sintéticos para fines académicos. Para producción se requiere cumplimiento Ley 1581/2012 e ISO 27001 — ver documentacion/CUMPLIMIENTO_LEY1581_ISO27001.md"* | Honestidad técnica, evita malentendidos |

### 4.2 Checklist rápido pre-entrega

- [ ] Verificar `data/raw/` **no contiene PII real** (solo sintéticos)
- [ ] Verificar `outputs/models/` **no expone datos de entrenamiento**
- [ ] Añadir disclaimer legal en README (ver arriba)
- [ ] Incluir sección "Consideraciones legales y de seguridad" en informe .docx
- [ ] Mencionar en presentación: "Diseñado para cumplimiento normativo desde arquitectura"
- [ ] Guardar este documento en `documentacion/CUMPLIMIENTO_LEY1581_ISO27001.md`

---

## 5. REVISIÓN FUTURA — Cuándo y cómo volver a esto

### 5.1 Triggers de revisión

| Evento | Acción | Responsable |
|--------|--------|-------------|
| **Post-entrega (semana 1 ago-2026)** | Revisar feedback jurados, actualizar hoja de ruta | Líder proyecto |
| **Inicio piloto con datos reales** | Ejecutar **Fase 1 completa** antes de cargar 1 solo dato real | Líder técnico + Legal |
| **Cada 3 meses** | Revisar avances Fase 2/3, actualizar análisis de riesgos | DPO + Líder técnico |
| **Incidente de seguridad** | Activar plan respuesta (A.5.24), registrar lección, actualizar controles | CSIRT |
| **Cambio normativo** (ej. reforma Ley 1581 2025) | Re-evaluar cumplimiento, actualizar políticas | Legal/DPO |
| **Auditoría interna (anual)** | Verificar efectividad controles, no conformidades, mejora | Auditor interno |

### 5.2 Métricas de seguimiento (KPIs de seguridad)

| KPI | Meta | Frecuencia | Fuente |
|-----|------|------------|--------|
| % Controles ISO 27001 implementados | 100% Fase 1 en 1 mes | Mensual | Checklist este doc |
| Tiempo detección incidente | < 1 hora | Continuo | Logs/Alertas |
| Tiempo respuesta ARCO | < 15 días hábiles | Por solicitud | Registro solicitudes |
| Vulnerabilidades críticas sin parchear | 0 | Semanal | `pip-audit`/Dependabot |
| Secretos detectados en código | 0 | Por commit | Pre-commit hooks |
| Entrenamiento seguridad equipo | 100% al año | Anual | Registro capacitaciones |

---

## 6. ARCHIVOS RELACIONADOS EN EL REPO

```
Capstone/
├── documentacion/
│   ├── CUMPLIMIENTO_LEY1581_ISO27001.md          ← ESTE ARCHIVO
│   ├── AUDITORIA_REVISION_2026-07-26.md          # Hallazgos técnicos previos
│   ├── Informe_Tecnico_LINE_APA.docx             # Incluye sección 4.7
│   └── LINE-Auditor-Medico-Digital.pptx          # Presentación del proyecto
├── README.md                                     # Disclaimer legal agregado
└── requirements.txt                              # Dependencias auditadas

LINE/
└── docs/                                         # Documentos de cumplimiento (creados)
    ├── POLITICA_SEGURIDAD.md                     # Creado — Fase 1, Acción 7
    ├── INVENTARIO_ACTIVOS.csv                    # Creado — Fase 1, Acción 8
    ├── ANALISIS_RIESGOS.md                       # Creado — Fase 1, Acción 9
    ├── AVISO_PRIVACIDAD.md                       # Creado — Fase 2, Acción 10
    ├── POLITICA_RETENCION.md                     # Creado — Fase 3, Acción 15
    └── CUMPLIMIENTO_LEY1581_ISO27001.md          # v1.1 — controles implementados

Pendientes a futuro (post-piloto): PIA_DATOS_SALUD.md, PROCEDIMIENTO_ARCO.md, PLAN_CONTINUIDAD.md
```

---

## 7. CONTACTOS Y ESCALAMIENTO

| Rol | Nombre | Contacto | Responsabilidad |
|-----|--------|----------|-----------------|
| **Líder Proyecto** | Jefersson Aldair Oliveros | - | Decisiones técnicas, priorización |
| **Legal / DPO (por designar)** | - | - | Ley 1581, PIA, RNBD, ARCO, contratos |
| **Líder Técnico / DevOps** | Iván Yesid Cristancho Plata | - | Controles ISO A.8, CI/CD, infra |
| **Equipo Desarrollo** | Jazmine, Isabella, Catalina | - | Implementación controles en código |

---

## 8. BITÁCORA DE CAMBIOS

| Versión | Fecha | Autor | Cambios |
|---------|-------|-------|---------|
| 1.0 | 30-jul-2026 | Jefersson Aldair Oliveros Monroy | Creación inicial basada en análisis Ley 1581 e ISO 27001:2022 |

---

> **Última actualización:** 30 de julio de 2026  
> **Próxima revisión programada:** Semana del 4 de agosto de 2026 (post-entrega)  
> **Ubicación:** `D:\PROYECTO CAPSTONE\Capstone\documentacion\CUMPLIMIENTO_LEY1581_ISO27001.md`

---

*Documento controlado. Revisar, validar y firmar por el equipo antes de uso oficial.*