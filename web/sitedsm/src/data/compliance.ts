export interface ComplianceMapping {
  requirement: string;
  meaning: string;
  feature: string;
  how: string;
}

export interface ComplianceGap {
  gap: string;
  risk: string;
  solution: string;
}

export interface ComplianceData {
  slug: string;
  badge: { es: string; en: string };
  headline: { es: string; en: string };
  subtitle: { es: string; en: string };
  what: {
    title: { es: string; en: string };
    text: { es: string; en: string };
  };
  who: {
    title: { es: string; en: string };
    items: { es: string; en: string }[];
  };
  penalties: {
    title: { es: string; en: string };
    items: { es: string; en: string }[];
  };
  mappings: {
    title: { es: string; en: string };
    subtitle: { es: string; en: string };
    items: {
      requirement: { es: string; en: string };
      meaning: { es: string; en: string };
      feature: { es: string; en: string };
      how: { es: string; en: string };
    }[];
  };
  auditor: {
    title: { es: string; en: string };
    questions: {
      question: { es: string; en: string };
      without: { es: string; en: string };
      with: { es: string; en: string };
    }[];
  };
  gaps: {
    title: { es: string; en: string };
    items: {
      gap: { es: string; en: string };
      risk: { es: string; en: string };
      solution: { es: string; en: string };
    }[];
  };
  timeline?: {
    title: { es: string; en: string };
    items: { date: string; event: { es: string; en: string } }[];
  };
  summary: {
    title: { es: string; en: string };
    text: { es: string; en: string };
  };
}

export const complianceData: ComplianceData[] = [
  // ─── NIS2 ────────────────────────────────────────────
  {
    slug: 'nis2',
    badge: { es: 'Directiva (UE) 2022/2555', en: 'Directive (EU) 2022/2555' },
    headline: {
      es: 'Por qué necesitas DSM Control para cumplir NIS2',
      en: 'Why you need DSM Control for NIS2 compliance',
    },
    subtitle: {
      es: 'NIS2 exige a las empresas europeas documentar y controlar sus activos TIC. DSM Control cubre los requisitos de gestión de activos, incidencias y trazabilidad que exige la directiva.',
      en: 'NIS2 requires European organizations to document and control their IT assets. DSM Control covers the asset management, incident handling, and traceability requirements mandated by the directive.',
    },
    what: {
      title: { es: 'Qué es NIS2', en: 'What is NIS2' },
      text: {
        es: 'NIS2 es la directiva europea de ciberseguridad que sustituye a la NIS original (2016). Amplía significativamente el número de organizaciones afectadas, introduce requisitos más estrictos y añade responsabilidad personal para la dirección. Es exigible desde octubre de 2024 y afecta a entidades esenciales e importantes en 18 sectores: energía, transporte, sanidad, manufactura, alimentación, servicios financieros, infraestructura digital y más.',
        en: 'NIS2 is the EU cybersecurity directive replacing the original NIS Directive (2016). It significantly expands the number of organizations in scope, introduces stricter requirements, and adds personal liability for management. It has been enforceable since October 2024 and affects essential and important entities across 18 sectors: energy, transport, health, manufacturing, food, financial services, digital infrastructure, and more.',
      },
    },
    who: {
      title: { es: 'Quién debe cumplir', en: 'Who must comply' },
      items: [
        {
          es: 'Entidades esenciales: grandes organizaciones en sectores críticos (energía, transporte, sanidad, banca, agua, infraestructura digital)',
          en: 'Essential entities: large organizations in critical sectors (energy, transport, health, banking, water, digital infrastructure)',
        },
        {
          es: 'Entidades importantes: organizaciones medianas (50+ empleados o 10M+ facturación) en los mismos sectores más manufactura, alimentación, química, servicios postales',
          en: 'Important entities: medium organizations (50+ employees or €10M+ revenue) in the same sectors plus manufacturing, food, chemicals, postal services',
        },
        {
          es: 'Cadena de suministro: cualquier empresa que provea servicios o productos TIC a entidades esenciales/importantes, independientemente de su tamaño',
          en: 'Supply chain: any company providing ICT services or products to essential/important entities, regardless of size',
        },
      ],
    },
    penalties: {
      title: { es: 'Sanciones', en: 'Penalties' },
      items: [
        { es: 'Entidades esenciales: hasta 10M EUR o 2% de la facturación global anual', en: 'Essential entities: up to €10M or 2% of global annual turnover' },
        { es: 'Entidades importantes: hasta 7M EUR o 1,4% de la facturación global anual', en: 'Important entities: up to €7M or 1.4% of global annual turnover' },
        { es: 'Responsabilidad personal: los órganos de dirección pueden ser personalmente responsables del incumplimiento', en: 'Personal liability: management bodies can be held personally liable for non-compliance' },
      ],
    },
    mappings: {
      title: { es: 'Requisitos NIS2 mapeados a DSM Control', en: 'NIS2 requirements mapped to DSM Control' },
      subtitle: {
        es: 'El Artículo 21 es el núcleo de NIS2. Exige medidas técnicas, operativas y organizativas para gestionar los riesgos de seguridad. Así cubre DSM Control cada requisito:',
        en: 'Article 21 is the core of NIS2. It requires technical, operational, and organizational measures to manage security risks. Here is how DSM Control covers each requirement:',
      },
      items: [
        {
          requirement: { es: 'Art. 21(a) — Políticas de análisis de riesgos', en: 'Art. 21(a) — Risk analysis policies' },
          meaning: { es: 'Documentar qué sistemas tienes y su exposición al riesgo', en: 'Document what systems you have and their risk exposure' },
          feature: { es: 'Inventario de activos con clasificación', en: 'Asset inventory with classification' },
          how: { es: 'Cada dispositivo registrado con tipo, fabricante, modelo, número de serie y clasificación de riesgo. Registro de activos exportable como base para el análisis de riesgos.', en: 'Every device registered with type, manufacturer, model, serial number, and risk classification. Exportable asset register as the foundation for risk analysis.' },
        },
        {
          requirement: { es: 'Art. 21(b) — Gestión de incidencias', en: 'Art. 21(b) — Incident handling' },
          meaning: { es: 'Detectar, reportar y responder a incidencias con procedimientos documentados', en: 'Detect, report, and respond to incidents with documented procedures' },
          feature: { es: 'Gestión de incidencias vinculadas a activos', en: 'Incident management with asset-linked tickets' },
          how: { es: 'Cada incidencia se crea contra un activo específico. La timeline muestra qué pasó, cuándo y qué acciones se tomaron. Las incidencias no pueden existir sin estar vinculadas a un dispositivo — por diseño.', en: 'Every incident is created against a specific asset. Timeline shows what happened, when, and what actions were taken. Incidents cannot exist without being linked to a device — by design.' },
        },
        {
          requirement: { es: 'Art. 21(c) — Continuidad de negocio', en: 'Art. 21(c) — Business continuity' },
          meaning: { es: 'Saber qué activos son críticos y planificar ante su fallo', en: 'Know what assets are critical and plan for failure' },
          feature: { es: 'Clasificación de criticidad + planes de mantenimiento', en: 'Criticality classification + maintenance plans' },
          how: { es: 'Los activos se clasifican por criticidad. Los planes de mantenimiento preventivo aseguran que los dispositivos críticos se mantienen proactivamente. El historial de incidencias por activo revela qué dispositivos son un riesgo.', en: 'Assets classified by criticality. Preventive maintenance schedules ensure critical devices are proactively maintained. Incident history per asset reveals reliability risks.' },
        },
        {
          requirement: { es: 'Art. 21(d) — Seguridad de la cadena de suministro', en: 'Art. 21(d) — Supply chain security' },
          meaning: { es: 'Saber qué hardware y software despliegas y de quién', en: 'Know what hardware and software you deploy and from whom' },
          feature: { es: 'Órdenes de compra con seguimiento de proveedores', en: 'Purchase orders with vendor tracking' },
          how: { es: 'Cada activo es trazable a una orden de compra, un proveedor y una fecha de entrega. El registro de proveedores da una visión completa de la cadena de suministro TIC.', en: 'Every asset traceable to a purchase order, vendor, and delivery date. Vendor registry provides complete ICT supply chain visibility.' },
        },
        {
          requirement: { es: 'Art. 21(e) — Seguridad en la adquisición y mantenimiento de sistemas', en: 'Art. 21(e) — Security in acquisition and maintenance' },
          meaning: { es: 'Seguimiento de dispositivos durante todo su ciclo de vida', en: 'Track devices through their entire lifecycle' },
          feature: { es: 'Gestión completa del ciclo de vida', en: 'Full lifecycle management' },
          how: { es: 'DSM Control gestiona el ciclo de vida completo: compra, almacén, asignación, incidencias, mantenimiento y baja. Cada etapa está documentada con timestamps, responsables y audit trail.', en: 'DSM Control manages the complete lifecycle: purchase, warehouse, assignment, incidents, maintenance, and decommission. Every stage documented with timestamps, owners, and audit trail.' },
        },
        {
          requirement: { es: 'Art. 21(f) — Evaluación de la eficacia de las medidas', en: 'Art. 21(f) — Assessing effectiveness of measures' },
          meaning: { es: 'Medir si tus controles funcionan', en: 'Measure whether your controls work' },
          feature: { es: 'Dashboard en tiempo real + audit trail', en: 'Real-time dashboard + audit trail' },
          how: { es: 'Dashboard con incidencias abiertas, cumplimiento SLA, distribución de estados de activos y adherencia al mantenimiento. Audit trail documenta cada acción sobre cada activo.', en: 'Dashboard with open incidents, SLA compliance, asset status distribution, and maintenance adherence. Audit trail documents every action on every asset.' },
        },
        {
          requirement: { es: 'Art. 21(i) — Gestión de activos', en: 'Art. 21(i) — Asset management' },
          meaning: { es: 'Mencionado explícitamente: la gestión de activos es una medida obligatoria', en: 'Explicitly mentioned: asset management is a required measure' },
          feature: { es: 'Funcionalidad principal del producto', en: 'Core product functionality' },
          how: { es: 'DSM Control está construido específicamente para la gestión de activos TIC. Inventario, seguimiento de asignaciones y permisos basados en roles son capacidades nativas.', en: 'DSM Control is purpose-built for IT asset management. Inventory, assignment tracking, and role-based permissions are native capabilities.' },
        },
      ],
    },
    auditor: {
      title: { es: 'Las 3 preguntas que hará tu auditor NIS2', en: 'The 3 questions your NIS2 auditor will ask' },
      questions: [
        {
          question: { es: '¿Qué dispositivos tiene tu empresa en su red?', en: 'What devices does your organization have on its network?' },
          without: { es: 'Hoja de cálculo, desactualizada, incompleta, sin fuente única de verdad', en: 'Spreadsheet, outdated, incomplete, no single source of truth' },
          with: { es: 'Inventario completo de activos con estado, ubicación y responsable — siempre actualizado', en: 'Complete asset inventory with status, location, and responsible person — always current' },
        },
        {
          question: { es: '¿Quién tiene acceso a qué dispositivos?', en: 'Who has access to which devices?' },
          without: { es: '"Déjame preguntar a RRHH" o "Creo que María tiene ese portátil"', en: '"Let me check with HR" or "I think Maria has that laptop"' },
          with: { es: 'Historial de asignaciones con trazabilidad temporal — quién tuvo qué, cuándo, y cada cambio documentado', en: 'Assignment history with temporal traceability — who had what, when, and every change documented' },
        },
        {
          question: { es: '¿Qué incidencias han tenido esos dispositivos?', en: 'What incidents have those devices had?' },
          without: { es: '"Teníamos tickets en el helpdesk pero no están vinculados a dispositivos específicos"', en: '"We had tickets in the helpdesk but they are not linked to specific devices"' },
          with: { es: 'Cada incidencia vinculada al activo específico, con timeline completa, acciones tomadas y resolución — exportable', en: 'Every incident linked to the specific asset, with full timeline, actions taken, and resolution — exportable' },
        },
      ],
    },
    gaps: {
      title: { es: 'Gaps de compliance que DSM Control cierra', en: 'Compliance gaps that DSM Control closes' },
      items: [
        {
          gap: { es: 'Sin inventario de activos', en: 'No asset inventory' },
          risk: { es: 'No puede demostrar cumplimiento del Art. 21(i)', en: 'Cannot demonstrate Article 21(i) compliance' },
          solution: { es: 'Inventario centralizado con todos los dispositivos, estado y metadatos', en: 'Centralized inventory with all devices, status, and metadata' },
        },
        {
          gap: { es: 'Incidencias separadas de los activos', en: 'Incidents tracked separately from assets' },
          risk: { es: 'No puede vincular incidencias a dispositivos para los reportes del Art. 23', en: 'Cannot link incidents to devices for Article 23 reporting' },
          solution: { es: 'Incidencias nativamente vinculadas a activos — sin integración necesaria', en: 'Incidents natively linked to assets — no integration needed' },
        },
        {
          gap: { es: 'Sin trazabilidad compra-a-baja', en: 'No purchase-to-decommission traceability' },
          risk: { es: 'No puede demostrar seguridad de la cadena de suministro (Art. 21(d))', en: 'Cannot demonstrate supply chain security (Article 21(d))' },
          solution: { es: 'Ciclo de vida completo desde orden de compra hasta baja con seguimiento de proveedores', en: 'Full lifecycle from purchase order to decommission with vendor tracking' },
        },
        {
          gap: { es: 'Sin audit trail', en: 'No audit trail' },
          risk: { es: 'No puede demostrar qué acciones se tomaron y por quién', en: 'Cannot prove what actions were taken and by whom' },
          solution: { es: 'Cada acción sobre cada activo registrada con usuario, timestamp y detalles', en: 'Every action on every asset logged with user, timestamp, and details' },
        },
        {
          gap: { es: 'Gaps en offboarding — dispositivos no recuperados', en: 'Offboarding gaps — devices not recovered' },
          risk: { es: 'Activos sin control en manos de exempleados', en: 'Uncontrolled assets in the field' },
          solution: { es: 'Gestión de asignaciones con workflows de offboarding y seguimiento de recuperación', en: 'Assignment management with offboarding workflows and recovery tracking' },
        },
        {
          gap: { es: 'Respuesta reactiva a incidencias', en: 'Reactive incident response' },
          risk: { es: 'No puede cumplir los plazos de reporte del Art. 23 (24h/72h)', en: 'Cannot meet Article 23 reporting timelines (24h/72h)' },
          solution: { es: 'Workflow estructurado de incidencias con timestamps en cada etapa', en: 'Structured incident workflow with timestamps for every stage' },
        },
      ],
    },
    timeline: {
      title: { es: 'Timeline NIS2', en: 'NIS2 Timeline' },
      items: [
        { date: 'Oct 2024', event: { es: 'NIS2 exigible en toda la UE', en: 'NIS2 enforceable across the EU' } },
        { date: '2025', event: { es: 'Primeros ciclos de auditoría. Empresas empiezan a recibir requerimientos.', en: 'First audit cycles. Companies start receiving requirements.' } },
        { date: 'Mar 2026', event: { es: 'DSM Control disponible — preparado para NIS2 desde el día 1', en: 'DSM Control available — NIS2 ready from day one' } },
        { date: 'Sep 2026', event: { es: 'Presión de compliance aumenta. Las empresas necesitan documentación AHORA.', en: 'Compliance pressure increases. Companies need documentation NOW.' } },
        { date: '2027+', event: { es: 'Enforcement pleno. NIS2 + DORA + CRA activos simultáneamente.', en: 'Full enforcement. NIS2 + DORA + CRA all active simultaneously.' } },
      ],
    },
    summary: {
      title: { es: 'Conclusión', en: 'Summary' },
      text: {
        es: 'DSM Control no es una herramienta genérica de ciberseguridad. Está construido específicamente para los requisitos que NIS2 Artículo 21(i) exige explícitamente: gestión de activos. Proporciona la trazabilidad documentada, auditable y a nivel de dispositivo que NIS2 requiere — vinculando cada dispositivo a su ciclo de vida, cada incidencia a su dispositivo, y cada acción a su audit trail. Para PYMEs que entran en el ámbito NIS2 por primera vez, DSM Control reemplaza la hoja de cálculo con un sistema preparado para compliance — sin el coste ni la complejidad de herramientas enterprise.',
        en: 'DSM Control is not a generic cybersecurity tool. It is purpose-built for the specific requirements that NIS2 Article 21(i) explicitly mandates: asset management. It provides the documented, auditable, device-level traceability that NIS2 requires — linking every device to its lifecycle, every incident to its device, and every action to its audit trail. For SMBs entering NIS2 scope for the first time, DSM Control replaces the spreadsheet with a compliance-ready system — without the cost or complexity of enterprise tools.',
      },
    },
  },

  // ─── ISO 27001 ───────────────────────────────────────
  {
    slug: 'iso27001',
    badge: { es: 'ISO/IEC 27001:2022', en: 'ISO/IEC 27001:2022' },
    headline: {
      es: 'Por qué necesitas DSM Control para certificarte en ISO 27001',
      en: 'Why you need DSM Control for ISO 27001 certification',
    },
    subtitle: {
      es: 'ISO 27001 exige controles de gestión de activos, incidencias, mantenimiento y baja segura. DSM Control cubre directamente 12 controles del Anexo A y soporta 8 más — el 21,5% de los 93 controles totales.',
      en: 'ISO 27001 requires controls for asset management, incidents, maintenance, and secure disposal. DSM Control directly addresses 12 Annex A controls and supports 8 more — 21.5% of all 93 controls.',
    },
    what: {
      title: { es: 'Qué es ISO 27001', en: 'What is ISO 27001' },
      text: {
        es: 'ISO 27001 es el estándar internacional para Sistemas de Gestión de Seguridad de la Información (SGSI). A diferencia de NIS2 o CRA, es voluntario — pero cada vez más exigido por clientes, partners, reguladores y aseguradoras como prueba de madurez en seguridad. Muchas organizaciones afectadas por NIS2 persiguen la certificación ISO 27001 como marco estructurado para demostrar cumplimiento. La Comisión Europea referencia explícitamente ISO 27001 como framework reconocido para NIS2.',
        en: 'ISO 27001 is the international standard for Information Security Management Systems (ISMS). Unlike NIS2 or CRA, it is voluntary — but increasingly required by clients, partners, regulators, and insurers as proof of security maturity. Many NIS2-affected organizations pursue ISO 27001 certification as a structured framework to demonstrate compliance. The European Commission explicitly references ISO 27001 as a recognized framework for NIS2.',
      },
    },
    who: {
      title: { es: 'Por qué importa para tu empresa', en: 'Why it matters for your company' },
      items: [
        { es: 'Clientes B2B exigen ISO 27001 antes de firmar contratos', en: 'B2B clients require ISO 27001 before signing contracts' },
        { es: 'Las pólizas de ciberseguro referencian ISO 27001 como requisito base', en: 'Cyber insurance policies reference ISO 27001 as a baseline requirement' },
        { es: 'NIS2 + ISO 27001 se complementan: las organizaciones usan ISO 27001 para implementar los requisitos NIS2', en: 'NIS2 + ISO 27001 complement each other: organizations use ISO 27001 to implement NIS2 requirements' },
        { es: 'Ventaja competitiva: la certificación diferencia a PYMEs de competidores que no pueden demostrar prácticas de seguridad', en: 'Competitive advantage: certification differentiates SMBs from competitors who cannot demonstrate security practices' },
      ],
    },
    penalties: {
      title: { es: 'Consecuencias del incumplimiento', en: 'Consequences of non-compliance' },
      items: [
        { es: 'Pérdida de certificación en auditorías de vigilancia (cada año)', en: 'Loss of certification in surveillance audits (every year)' },
        { es: 'Pérdida de contratos con clientes que exigen ISO 27001', en: 'Loss of contracts with clients that require ISO 27001' },
        { es: 'No-conformidades en controles de activos son de las más citadas por auditores', en: 'Non-conformities in asset controls are among the most cited by auditors' },
      ],
    },
    mappings: {
      title: { es: 'Controles ISO 27001 mapeados a DSM Control', en: 'ISO 27001 controls mapped to DSM Control' },
      subtitle: {
        es: 'ISO 27001:2022 Anexo A contiene 93 controles. DSM Control cubre directamente los siguientes:',
        en: 'ISO 27001:2022 Annex A contains 93 controls. DSM Control directly covers the following:',
      },
      items: [
        {
          requirement: { es: 'A.5.9 — Inventario de activos', en: 'A.5.9 — Inventory of assets' },
          meaning: { es: '"Se debe identificar y mantener un inventario de activos con sus propietarios"', en: '"An inventory of assets including owners shall be identified and maintained"' },
          feature: { es: 'Inventario completo de activos TIC', en: 'Complete IT asset inventory' },
          how: { es: 'Inventario con propietario (usuario asignado), ubicación, estado y metadatos. Este es el control más importante para la propuesta de valor de DSM Control.', en: 'Inventory with owner (assigned user), location, status, and metadata. This is the single most important control for DSM Control\'s value proposition.' },
        },
        {
          requirement: { es: 'A.5.11 — Devolución de activos', en: 'A.5.11 — Return of assets' },
          meaning: { es: 'El personal debe devolver todos los activos al terminar su relación laboral', en: 'Personnel shall return all assets upon termination of employment' },
          feature: { es: 'Gestión de asignaciones con offboarding', en: 'Assignment management with offboarding' },
          how: { es: 'Cuando un empleado se va, DSM Control muestra exactamente qué dispositivos tiene. La recuperación se puede rastrear y verificar.', en: 'When an employee leaves, DSM Control shows exactly what devices they have. Recovery can be tracked and verified.' },
        },
        {
          requirement: { es: 'A.5.24–A.5.28 — Gestión de incidencias de seguridad', en: 'A.5.24–A.5.28 — Security incident management' },
          meaning: { es: 'Planificación, evaluación, respuesta, aprendizaje y recopilación de evidencias de incidencias', en: 'Planning, assessment, response, learning, and evidence collection for incidents' },
          feature: { es: 'Gestión de incidencias con vinculación a activos', en: 'Incident management with asset linking' },
          how: { es: 'Workflow completo de incidencias: creación contra activo, clasificación, asignación, resolución. Timeline con timestamps. Historial por activo revela patrones. Audit trail preserva evidencias.', en: 'Complete incident workflow: creation against asset, classification, assignment, resolution. Timeline with timestamps. History per asset reveals patterns. Audit trail preserves evidence.' },
        },
        {
          requirement: { es: 'A.7.9 — Seguridad de activos fuera de las instalaciones', en: 'A.7.9 — Security of assets off-premises' },
          meaning: { es: 'Los activos fuera de las instalaciones deben estar protegidos', en: 'Off-site assets shall be protected' },
          feature: { es: 'Seguimiento de asignaciones y envíos', en: 'Assignment and shipment tracking' },
          how: { es: 'Seguimiento de qué dispositivos están fuera (empleados remotos, otras sedes). Módulo de envíos con cadena de custodia.', en: 'Track which devices are off-site (remote employees, other locations). Shipment module with chain of custody.' },
        },
        {
          requirement: { es: 'A.7.13 — Mantenimiento de equipos', en: 'A.7.13 — Equipment maintenance' },
          meaning: { es: 'Los equipos deben mantenerse correctamente para asegurar su disponibilidad', en: 'Equipment shall be maintained correctly to ensure availability' },
          feature: { es: 'Mantenimiento preventivo y correctivo', en: 'Preventive and corrective maintenance' },
          how: { es: 'Módulo de mantenimiento con calendario, programación y seguimiento de finalización. Historial de mantenimiento por activo como registro auditable.', en: 'Maintenance module with calendar, scheduling, and completion tracking. Maintenance history per asset as auditable record.' },
        },
        {
          requirement: { es: 'A.7.14 — Baja segura o reutilización de equipos', en: 'A.7.14 — Secure disposal or re-use of equipment' },
          meaning: { es: 'Verificar que los datos se han eliminado antes de la baja o reutilización', en: 'Verify data has been removed prior to disposal or re-use' },
          feature: { es: 'Etapa de baja en el ciclo de vida', en: 'Decommission lifecycle stage' },
          how: { es: 'La etapa de baja documenta cuándo y cómo se retiró un dispositivo. Campos personalizados para método de sanitización y certificado de destrucción.', en: 'Decommission stage documents when and how a device was retired. Custom fields for sanitization method and destruction certificate.' },
        },
        {
          requirement: { es: 'A.8.1 — Dispositivos de usuario final', en: 'A.8.1 — User endpoint devices' },
          meaning: { es: 'Proteger la información en dispositivos de usuario', en: 'Protect information on user endpoint devices' },
          feature: { es: 'Inventario de endpoints', en: 'Endpoint inventory' },
          how: { es: 'Inventario completo de todos los endpoints (portátiles, teléfonos, tablets) con usuario asignado, ubicación e historial de incidencias.', en: 'Complete inventory of all endpoints (laptops, phones, tablets) with assigned user, location, and incident history.' },
        },
      ],
    },
    auditor: {
      title: { es: 'Qué necesita ver el auditor ISO 27001', en: 'What the ISO 27001 auditor needs to see' },
      questions: [
        {
          question: { es: 'Muéstrame tu inventario de activos', en: 'Show me your asset inventory' },
          without: { es: 'Archivo Excel, posiblemente desactualizado, sin seguimiento de propietarios', en: 'Excel file, possibly outdated, no owner tracking' },
          with: { es: 'Inventario en vivo con propietarios, ubicaciones y estado — siempre actualizado', en: 'Live inventory with owners, locations, and status — always current' },
        },
        {
          question: { es: '¿Cómo verificáis que los activos se devuelven cuando un empleado se va?', en: 'How do you verify assets are returned when employees leave?' },
          without: { es: 'Proceso manual por email, sin verificación', en: 'Manual email process, no verification' },
          with: { es: 'Workflow de offboarding con lista de dispositivos por empleado y confirmación de recuperación', en: 'Offboarding workflow with device list per employee and recovery confirmation' },
        },
        {
          question: { es: 'Muéstrame los registros de mantenimiento de los equipos críticos', en: 'Show me maintenance records for critical equipment' },
          without: { es: 'Registros en papel o emails sueltos', en: 'Paper records or ad-hoc emails' },
          with: { es: 'Módulo de mantenimiento con tareas programadas y completadas por activo', en: 'Maintenance module with scheduled and completed tasks per asset' },
        },
        {
          question: { es: 'Muéstrame el audit trail', en: 'Show me your audit trail' },
          without: { es: 'No existe', en: 'Does not exist' },
          with: { es: 'Cada acción sobre cada activo registrada con usuario, timestamp y detalles', en: 'Every action on every asset logged with user, timestamp, and details' },
        },
      ],
    },
    gaps: {
      title: { es: 'No-conformidades habituales que DSM Control evita', en: 'Common non-conformities that DSM Control prevents' },
      items: [
        {
          gap: { es: 'Inventario no mantenido (A.5.9)', en: 'Inventory not maintained (A.5.9)' },
          risk: { es: 'No-conformidad mayor — el control más auditado', en: 'Major non-conformity — the most audited control' },
          solution: { es: 'Sistema que impone el registro y rastrea cambios automáticamente', en: 'System that enforces registration and tracks changes automatically' },
        },
        {
          gap: { es: 'Sin proceso de devolución verificable (A.5.11)', en: 'No verifiable return process (A.5.11)' },
          risk: { es: 'No-conformidad — activos sin controlar en manos de exempleados', en: 'Non-conformity — uncontrolled assets held by former employees' },
          solution: { es: 'Seguimiento de asignaciones que muestra dispositivos pendientes por empleado', en: 'Assignment tracking showing outstanding devices per employee' },
        },
        {
          gap: { es: 'Sin registros de mantenimiento (A.7.13)', en: 'No maintenance records (A.7.13)' },
          risk: { es: 'No-conformidad — no puede demostrar que los equipos se mantienen', en: 'Non-conformity — cannot demonstrate equipment is maintained' },
          solution: { es: 'Calendario de mantenimiento con registros de completado', en: 'Maintenance calendar with completion records' },
        },
        {
          gap: { es: 'Audit trail inexistente (A.5.28)', en: 'Non-existent audit trail (A.5.28)' },
          risk: { es: 'No-conformidad — no puede preservar evidencias', en: 'Non-conformity — cannot preserve evidence' },
          solution: { es: 'Audit trail inmutable — cada cambio registrado', en: 'Immutable audit trail — every change logged' },
        },
      ],
    },
    summary: {
      title: { es: 'Conclusión', en: 'Summary' },
      text: {
        es: 'ISO 27001 es el estándar de seguridad de la información más adoptado del mundo. Para organizaciones que buscan la certificación — especialmente PYMEs — los controles de gestión de activos e incidencias (A.5.9, A.5.11, A.5.24–A.5.28, A.7.13, A.7.14, A.8.1) están entre los más auditados y los que más no-conformidades generan. DSM Control cubre directamente 12 controles del Anexo A y soporta 8 más. Para empresas que también están afectadas por NIS2, DSM Control proporciona una única plataforma que satisface ambos frameworks simultáneamente. DSM Control es la columna vertebral de gestión de activos de tu SGSI.',
        en: 'ISO 27001 is the most widely adopted information security standard in the world. For organizations pursuing certification — especially SMBs — asset management and incident controls (A.5.9, A.5.11, A.5.24–A.5.28, A.7.13, A.7.14, A.8.1) are among the most audited and most frequently cited as non-conformities. DSM Control directly addresses 12 Annex A controls and supports 8 more. For companies also affected by NIS2, DSM Control provides a single platform that satisfies both frameworks simultaneously. DSM Control is the asset management backbone of your ISMS.',
      },
    },
  },

  // ─── CRA ─────────────────────────────────────────────
  {
    slug: 'cra',
    badge: { es: 'Reglamento (UE) 2024/2847', en: 'Regulation (EU) 2024/2847' },
    headline: {
      es: 'Por qué necesitas DSM Control para cumplir el CRA',
      en: 'Why you need DSM Control for CRA compliance',
    },
    subtitle: {
      es: 'El Cyber Resilience Act obliga a los fabricantes a divulgar vulnerabilidades. Las empresas que usan esos productos necesitan responder en minutos, no en días. DSM Control te dice en 30 segundos si estás afectado.',
      en: 'The Cyber Resilience Act requires manufacturers to disclose vulnerabilities. Companies using those products need to respond in minutes, not days. DSM Control tells you in 30 seconds if you are affected.',
    },
    what: {
      title: { es: 'Qué es el CRA', en: 'What is the CRA' },
      text: {
        es: 'El Cyber Resilience Act (CRA) es un reglamento de la UE que establece requisitos de ciberseguridad para productos con elementos digitales — cualquier hardware o software que se conecte a una red. A diferencia de NIS2 (que afecta a las organizaciones que usan tecnología), el CRA afecta a las que fabrican, importan o distribuyen productos tecnológicos. Las obligaciones de reporte empiezan en septiembre de 2026 y el cumplimiento total se exige en diciembre de 2027.',
        en: 'The Cyber Resilience Act (CRA) is an EU regulation establishing cybersecurity requirements for products with digital elements — any hardware or software that connects to a network. Unlike NIS2 (which targets organizations that use technology), the CRA targets those that manufacture, import, or distribute technology products. Reporting obligations start September 2026 and full compliance is required by December 2027.',
      },
    },
    who: {
      title: { es: 'A quién afecta', en: 'Who is affected' },
      items: [
        { es: 'Fabricantes de productos con elementos digitales (hardware con software embebido, software, dispositivos IoT)', en: 'Manufacturers of products with digital elements (hardware with embedded software, software, IoT devices)' },
        { es: 'Importadores que colocan productos de fuera de la UE en el mercado europeo', en: 'Importers placing products from outside the EU on the European market' },
        { es: 'Distribuidores que hacen disponibles productos en el mercado de la UE', en: 'Distributors making products available on the EU market' },
        { es: 'Cualquier empresa que USE productos con elementos digitales — porque recibirá notificaciones de vulnerabilidades de los fabricantes', en: 'Any company that USES products with digital elements — because they will receive vulnerability notifications from manufacturers' },
      ],
    },
    penalties: {
      title: { es: 'Sanciones', en: 'Penalties' },
      items: [
        { es: 'Hasta 15M EUR o 2,5% de la facturación global anual por incumplimiento de requisitos esenciales', en: 'Up to €15M or 2.5% of global annual turnover for non-compliance with essential requirements' },
        { es: 'Hasta 10M EUR o 2% por otras infracciones', en: 'Up to €10M or 2% for other violations' },
        { es: 'Hasta 5M EUR o 1% por proporcionar información incorrecta', en: 'Up to €5M or 1% for providing incorrect information' },
      ],
    },
    mappings: {
      title: { es: 'Impacto del CRA y cómo responde DSM Control', en: 'CRA impact and how DSM Control responds' },
      subtitle: {
        es: 'El CRA crea una nueva realidad: los fabricantes divulgarán vulnerabilidades y tu empresa necesita responder. Estos son los escenarios críticos:',
        en: 'The CRA creates a new reality: manufacturers will disclose vulnerabilities and your company needs to respond. These are the critical scenarios:',
      },
      items: [
        {
          requirement: { es: 'Un fabricante divulga una vulnerabilidad', en: 'A manufacturer discloses a vulnerability' },
          meaning: { es: '"Hay una vulnerabilidad crítica en los routers TapLink RX-500. ¿Tenemos alguno? ¿Dónde?"', en: '"There is a critical vulnerability in TapLink RX-500 routers. Do we have any? Where?"' },
          feature: { es: 'Búsqueda por fabricante y modelo', en: 'Search by manufacturer and model' },
          how: { es: 'Filtra por fabricante + modelo. En 30 segundos: cuántas unidades, dónde están, quién las tiene. Crea incidencias para todos los dispositivos afectados inmediatamente.', en: 'Filter by manufacturer + model. In 30 seconds: how many units, where they are, who has them. Create incidents for all affected devices immediately.' },
        },
        {
          requirement: { es: 'Un fabricante publica una actualización de firmware', en: 'A manufacturer issues a firmware update' },
          meaning: { es: 'Necesitas identificar todos los dispositivos afectados y aplicar la actualización', en: 'You need to identify all affected devices and apply the update' },
          feature: { es: 'Tareas de mantenimiento vinculadas a activos', en: 'Maintenance tasks linked to assets' },
          how: { es: 'Filtra dispositivos afectados, crea tarea de mantenimiento, rastrea estado de actualización por dispositivo. Dashboard muestra porcentaje de completado.', en: 'Filter affected devices, create maintenance task, track update status per device. Dashboard shows completion percentage.' },
        },
        {
          requirement: { es: 'Un fabricante retira un producto del mercado', en: 'A manufacturer recalls a product' },
          meaning: { es: 'Necesitas identificar y retirar del servicio todas las unidades', en: 'You need to identify and remove all units from service' },
          feature: { es: 'Workflow de baja con trazabilidad', en: 'Decommission workflow with traceability' },
          how: { es: 'Lista inmediata de dispositivos con ubicaciones y usuarios asignados. Workflow de baja para cada unidad. Audit trail completo del proceso de retirada.', en: 'Immediate device list with locations and assigned users. Decommission workflow for each unit. Full audit trail of the recall process.' },
        },
        {
          requirement: { es: 'Un auditor pregunta cómo respondiste a una divulgación CRA', en: 'An auditor asks how you responded to a CRA disclosure' },
          meaning: { es: '"Cuando se publicó el aviso de vulnerabilidad del producto X en octubre, ¿cómo respondió tu organización?"', en: '"When the vulnerability advisory for product X was published in October, how did your organization respond?"' },
          feature: { es: 'Timeline de incidencias con evidencia', en: 'Incident timeline with evidence' },
          how: { es: 'Incidencia creada el 3 de octubre a las 09:14. Vinculada a 8 dispositivos. Firmware actualizado en los 8 para el 5 de octubre. Timeline exportable con cada paso documentado.', en: 'Incident created October 3rd at 09:14. Linked to 8 devices. Firmware updated on all 8 by October 5th. Exportable timeline with every step documented.' },
        },
      ],
    },
    auditor: {
      title: { es: 'La pregunta que no podrás responder sin DSM Control', en: 'The question you cannot answer without DSM Control' },
      questions: [
        {
          question: { es: '¿Cuántos dispositivos del modelo X tenemos?', en: 'How many devices of model X do we have?' },
          without: { es: 'Llamadas a cada oficina, revisar órdenes de compra en emails, días de investigación', en: 'Phone calls to each office, checking purchase orders in email, days of investigation' },
          with: { es: 'Filtro por fabricante + modelo. Resultado en 30 segundos con ubicaciones y usuarios', en: 'Filter by manufacturer + model. Result in 30 seconds with locations and users' },
        },
        {
          question: { es: '¿Cuáles de nuestros routers tienen el firmware 4.2.1 vulnerable?', en: 'Which of our routers are running vulnerable firmware 4.2.1?' },
          without: { es: 'Imposible saberlo sin revisar físicamente cada router', en: 'Impossible to know without physically checking each router' },
          with: { es: 'Campo personalizado "version_firmware" filtrado a "4.2.1". Resultado: 5 dispositivos identificados', en: 'Custom field "firmware_version" filtered to "4.2.1". Result: 5 devices identified' },
        },
        {
          question: { es: '¿Qué hicimos cuando el fabricante publicó el aviso de seguridad?', en: 'What did we do when the manufacturer published the security advisory?' },
          without: { es: 'Sin evidencia documentada de la respuesta', en: 'No documented evidence of response' },
          with: { es: 'Incidencia con timeline completa: detección, dispositivos afectados, acciones tomadas, resolución. Todo exportable.', en: 'Incident with full timeline: detection, affected devices, actions taken, resolution. All exportable.' },
        },
      ],
    },
    gaps: {
      title: { es: 'Gaps críticos que el CRA expone', en: 'Critical gaps that the CRA exposes' },
      items: [
        {
          gap: { es: 'Sin inventario por fabricante y modelo', en: 'No inventory by manufacturer and model' },
          risk: { es: 'No puedes responder a divulgaciones de vulnerabilidades del CRA', en: 'Cannot respond to CRA vulnerability disclosures' },
          solution: { es: 'Inventario con fabricante, modelo, número de serie y versión de firmware por dispositivo', en: 'Inventory with manufacturer, model, serial number, and firmware version per device' },
        },
        {
          gap: { es: 'Sin capacidad de respuesta rápida', en: 'No rapid response capability' },
          risk: { es: 'Días o semanas para evaluar exposición a una vulnerabilidad', en: 'Days or weeks to assess exposure to a vulnerability' },
          solution: { es: 'Búsqueda instantánea + creación masiva de incidencias para dispositivos afectados', en: 'Instant search + bulk incident creation for affected devices' },
        },
        {
          gap: { es: 'Sin evidencia de respuesta a incidentes', en: 'No evidence of incident response' },
          risk: { es: 'No puede demostrar al auditor NIS2 cómo respondió a las divulgaciones CRA', en: 'Cannot demonstrate to NIS2 auditor how it responded to CRA disclosures' },
          solution: { es: 'Timeline de incidencias con timestamps, dispositivos afectados y acciones documentadas', en: 'Incident timeline with timestamps, affected devices, and documented actions' },
        },
        {
          gap: { es: 'Sin seguimiento de actualizaciones de firmware', en: 'No firmware update tracking' },
          risk: { es: 'Dispositivos vulnerables sin parchear durante semanas', en: 'Vulnerable devices unpatched for weeks' },
          solution: { es: 'Tareas de mantenimiento por dispositivo con estado de completado', en: 'Maintenance tasks per device with completion status' },
        },
      ],
    },
    timeline: {
      title: { es: 'Timeline CRA', en: 'CRA Timeline' },
      items: [
        { date: 'Dic 2024', event: { es: 'CRA entra en vigor', en: 'CRA enters into force' } },
        { date: 'Mar 2026', event: { es: 'DSM Control disponible — 6 meses antes de las obligaciones CRA', en: 'DSM Control available — 6 months before CRA obligations' } },
        { date: 'Sep 2026', event: { es: 'Obligaciones de reporte activas. Los fabricantes empiezan a divulgar vulnerabilidades a ENISA.', en: 'Reporting obligations active. Manufacturers start disclosing vulnerabilities to ENISA.' } },
        { date: 'Dic 2027', event: { es: 'Cumplimiento total exigido. Todos los productos en el mercado UE deben cumplir los requisitos CRA.', en: 'Full compliance required. All products on the EU market must meet CRA requirements.' } },
      ],
    },
    summary: {
      title: { es: 'Conclusión', en: 'Summary' },
      text: {
        es: 'El CRA crea una nueva realidad: los fabricantes estarán obligados a divulgar vulnerabilidades, y las organizaciones que usen esos productos necesitarán responder rápidamente y documentar su respuesta. Esto transforma la gestión de activos TIC de un "está bien tenerlo" a una capacidad crítica para el compliance. DSM Control proporciona la capa esencial que conecta las divulgaciones CRA con los dispositivos reales de tu organización: saber qué tienes, dónde está, responder rápido y demostrar que respondiste. Las obligaciones de reporte CRA empiezan en septiembre de 2026. El momento de prepararse es ahora.',
        en: 'The CRA creates a new reality: manufacturers will be required to disclose vulnerabilities, and organizations using those products will need to respond rapidly and document their response. This transforms IT asset management from a "nice to have" into a compliance-critical capability. DSM Control provides the essential layer connecting CRA disclosures to actual devices in your organization: know what you have, where it is, respond fast, and prove you responded. CRA reporting obligations start September 2026. The time to prepare is now.',
      },
    },
  },

  // ─── DORA ───────────────────────────────────────────
  {
    slug: 'dora',
    badge: { es: 'Reglamento (UE) 2022/2554', en: 'Regulation (EU) 2022/2554' },
    headline: {
      es: 'Por que necesitas DSM Control para cumplir DORA',
      en: 'Why you need DSM Control for DORA compliance',
    },
    subtitle: {
      es: 'DORA exige a las entidades financieras identificar, clasificar y documentar todos sus activos TIC. DSM Control proporciona el inventario, la gestion de incidencias y la trazabilidad que DORA requiere.',
      en: 'DORA requires financial entities to identify, classify, and document all ICT assets. DSM Control provides the inventory, incident management, and traceability that DORA demands.',
    },
    what: {
      title: { es: 'Que es DORA', en: 'What is DORA' },
      text: {
        es: 'El Digital Operational Resilience Act (DORA) es un reglamento de la UE que establece un marco integral para la resiliencia operativa digital del sector financiero. Exige que las entidades financieras puedan resistir, responder y recuperarse de todo tipo de perturbaciones y amenazas relacionadas con las TIC. A diferencia de NIS2 (que cubre 18 sectores), DORA es especifico del sector financiero con requisitos mas profundos y prescriptivos. Es aplicable desde el 17 de enero de 2025.',
        en: 'The Digital Operational Resilience Act (DORA) is an EU regulation establishing a comprehensive framework for digital operational resilience in the financial sector. It requires financial entities to withstand, respond to, and recover from all types of ICT-related disruptions and threats. Unlike NIS2 (which covers 18 sectors broadly), DORA is sector-specific to finance with deeper, more prescriptive requirements. It has been applicable since January 17, 2025.',
      },
    },
    who: {
      title: { es: 'Quien debe cumplir', en: 'Who must comply' },
      items: [
        { es: 'Bancos e instituciones de credito', en: 'Banks and credit institutions' },
        { es: 'Companias de seguros y reaseguros', en: 'Insurance and reinsurance companies' },
        { es: 'Empresas de inversion, gestoras de fondos, fintechs', en: 'Investment firms, fund managers, fintechs' },
        { es: 'Instituciones de pago, entidades de dinero electronico, proveedores de servicios de criptoactivos', en: 'Payment institutions, e-money institutions, crypto-asset service providers' },
        { es: 'Proveedores de servicios TIC criticos para el sector financiero (cloud, SaaS, centros de datos)', en: 'Critical ICT third-party providers to the financial sector (cloud, SaaS, data centers)' },
      ],
    },
    penalties: {
      title: { es: 'Sanciones', en: 'Penalties' },
      items: [
        { es: 'Sanciones determinadas por las autoridades nacionales competentes, proporcionadas a la gravedad', en: 'Penalties determined by national competent authorities, proportionate to severity' },
        { es: 'Proveedores TIC criticos: hasta 5M EUR o 1% de la facturacion media diaria mundial durante hasta 6 meses', en: 'Critical ICT providers: up to €5M or 1% of average daily worldwide turnover for up to 6 months' },
        { es: 'Los organos de direccion son personalmente responsables del cumplimiento de la gestion de riesgos TIC', en: 'Management bodies are personally responsible for ICT risk management compliance' },
        { es: 'Las autoridades supervisoras pueden restringir actividades o retirar autorizaciones', en: 'Supervisory authorities can restrict activities or withdraw authorizations' },
      ],
    },
    mappings: {
      title: { es: 'Requisitos DORA mapeados a DSM Control', en: 'DORA requirements mapped to DSM Control' },
      subtitle: {
        es: 'DORA se estructura en 5 pilares. DSM Control proporciona capacidades directas para los tres mas relevantes: gestion de riesgos TIC, gestion de incidencias y riesgo de terceros.',
        en: 'DORA is structured around 5 pillars. DSM Control provides direct capabilities for the three most relevant: ICT risk management, incident management, and third-party risk.',
      },
      items: [
        {
          requirement: { es: 'Art. 8(1) — Identificacion de activos TIC', en: 'Art. 8(1) — ICT asset identification' },
          meaning: { es: '"Las entidades financieras identificaran, clasificaran y documentaran adecuadamente todos los activos TIC"', en: '"Financial entities shall identify, classify and adequately document all ICT assets"' },
          feature: { es: 'Inventario completo de activos TIC', en: 'Complete ICT asset inventory' },
          how: { es: 'Inventario centralizado con clasificacion, propietario, ubicacion, estado y metadatos completos. Este es el requisito fundacional del marco de gestion de riesgos de DORA.', en: 'Centralized inventory with classification, owner, location, status, and full metadata. This is the foundational requirement of DORA\'s risk management framework.' },
        },
        {
          requirement: { es: 'Art. 8(4) — Identificacion continua de riesgos TIC', en: 'Art. 8(4) — Continuous ICT risk identification' },
          meaning: { es: 'Identificar fuentes de riesgo TIC y evaluar amenazas y vulnerabilidades', en: 'Identify ICT risk sources and assess threats and vulnerabilities' },
          feature: { es: 'Inventario por fabricante, modelo y firmware', en: 'Inventory by manufacturer, model, and firmware' },
          how: { es: 'Cuando se divulga una vulnerabilidad, busca por fabricante + modelo + version de firmware. Los dispositivos afectados se identifican en segundos, no en dias.', en: 'When a vulnerability is disclosed, search by manufacturer + model + firmware version. Affected devices identified in seconds, not days.' },
        },
        {
          requirement: { es: 'Art. 9 — Proteccion y prevencion', en: 'Art. 9 — Protection and prevention' },
          meaning: { es: 'Monitorizar y controlar continuamente la seguridad y funcionamiento de los sistemas TIC', en: 'Continuously monitor and control the security and functioning of ICT systems' },
          feature: { es: 'Ciclo de vida + mantenimiento preventivo', en: 'Lifecycle management + preventive maintenance' },
          how: { es: 'Seguimiento del estado de cada activo, planes de mantenimiento programados, alertas de garantia y edad. La infraestructura de red (routers, switches, firewalls) se documenta con ubicacion y conexiones.', en: 'Status tracking per asset, scheduled maintenance plans, warranty and age alerts. Network infrastructure (routers, switches, firewalls) documented with location and connections.' },
        },
        {
          requirement: { es: 'Art. 17 — Proceso de gestion de incidencias TIC', en: 'Art. 17 — ICT incident management process' },
          meaning: { es: 'Definir y establecer un proceso para detectar, gestionar y notificar incidencias TIC', en: 'Define and establish a process to detect, manage, and notify ICT-related incidents' },
          feature: { es: 'Workflow estructurado de incidencias', en: 'Structured incident workflow' },
          how: { es: 'Incidencia creada contra activo especifico, clasificacion, asignacion a tecnico, seguimiento de estado, resolucion. Cada paso con timestamp. Timeline completa exportable.', en: 'Incident created against specific asset, classification, assignment to technician, status tracking, resolution. Every step timestamped. Full timeline exportable.' },
        },
        {
          requirement: { es: 'Art. 19 — Notificacion de incidencias graves', en: 'Art. 19 — Major incident reporting' },
          meaning: { es: 'Notificacion inicial en 4 horas, informe intermedio en 72 horas, informe final en 1 mes', en: 'Initial notification within 4 hours, intermediate report within 72 hours, final report within 1 month' },
          feature: { es: 'Timeline de incidencias con timestamps', en: 'Incident timeline with timestamps' },
          how: { es: 'El timestamp de creacion documenta cuando se identifico la incidencia. La vinculacion a activos muestra que sistemas fueron afectados. La timeline proporciona la base de evidencia para el reporte regulatorio.', en: 'Creation timestamp documents when incident was identified. Asset linkage shows which systems were affected. Timeline provides the evidence base for regulatory reporting.' },
        },
        {
          requirement: { es: 'Art. 28 — Riesgo de terceros TIC', en: 'Art. 28 — ICT third-party risk' },
          meaning: { es: 'Mantener un registro de acuerdos contractuales con proveedores TIC y evaluar sus riesgos', en: 'Maintain a register of contractual arrangements with ICT providers and assess their risks' },
          feature: { es: 'Registro de proveedores + trazabilidad de activos', en: 'Vendor registry + asset traceability' },
          how: { es: 'Cada activo es trazable a su proveedor y orden de compra. Si un proveedor sufre un incidente de seguridad, sabes inmediatamente que activos estan afectados.', en: 'Every asset traceable to its vendor and purchase order. If a vendor suffers a security incident, you immediately know which assets are affected.' },
        },
      ],
    },
    auditor: {
      title: { es: 'Que espera el supervisor en una inspeccion DORA', en: 'What the supervisor expects in a DORA inspection' },
      questions: [
        {
          question: { es: 'Muestrame tu registro de activos TIC (Articulo 8)', en: 'Show me your ICT asset register (Article 8)' },
          without: { es: 'Archivo Excel, posiblemente desactualizado, sin clasificacion', en: 'Excel file, possibly outdated, no classification' },
          with: { es: 'Inventario en vivo con clasificacion, propietarios y ubicaciones — siempre actualizado', en: 'Live inventory with classification, owners, and locations — always current' },
        },
        {
          question: { es: 'Como identificais que activos estan afectados cuando se divulga una vulnerabilidad?', en: 'How do you identify which assets are affected when a vulnerability is disclosed?' },
          without: { es: 'Investigacion manual, llamadas, busquedas en hojas de calculo. Dias.', en: 'Manual investigation, phone calls, spreadsheet searches. Days.' },
          with: { es: 'Filtro por fabricante + modelo + firmware. Resultado en segundos.', en: 'Filter by manufacturer + model + firmware. Result in seconds.' },
        },
        {
          question: { es: 'Cual es vuestra exposicion al proveedor X? (Articulo 28)', en: 'What is your exposure to provider X? (Article 28)' },
          without: { es: '"Dejame comprobarlo..." — dias de investigacion', en: '"Let me check..." — days of investigation' },
          with: { es: 'Filtro de activos por proveedor. Visibilidad inmediata: cuantos dispositivos, donde, quien los tiene.', en: 'Filter assets by vendor. Instant visibility: how many devices, where, who has them.' },
        },
        {
          question: { es: 'Demuestrame el proceso de gestion de incidencias TIC (Articulo 17)', en: 'Demonstrate your ICT incident management process (Article 17)' },
          without: { es: 'Emails y tickets en un sistema separado, sin vincular a activos', en: 'Emails and tickets in a separate system, not linked to assets' },
          with: { es: 'Incidencia creada contra activo especifico, timeline completa con cada accion documentada', en: 'Incident created against specific asset, full timeline with every action documented' },
        },
      ],
    },
    gaps: {
      title: { es: 'Gaps de compliance que DORA expone', en: 'Compliance gaps that DORA exposes' },
      items: [
        {
          gap: { es: 'Sin inventario de activos TIC', en: 'No ICT asset inventory' },
          risk: { es: 'No puede demostrar cumplimiento del Articulo 8 — el requisito fundacional', en: 'Cannot demonstrate Article 8 compliance — the foundational requirement' },
          solution: { es: 'Inventario centralizado con todos los activos TIC, clasificacion, propietarios y metadatos', en: 'Centralized inventory with all ICT assets, classification, owners, and metadata' },
        },
        {
          gap: { es: 'Activos sin clasificar por criticidad', en: 'Assets not classified by criticality' },
          risk: { es: 'No puede evaluar el impacto operativo de incidencias (Articulo 18)', en: 'Cannot assess operational impact of incidents (Article 18)' },
          solution: { es: 'Campos de clasificacion de activos con niveles de criticidad', en: 'Asset classification fields with criticality levels' },
        },
        {
          gap: { es: 'Incidencias no vinculadas a activos', en: 'Incidents not linked to assets' },
          risk: { es: 'No puede demostrar que sistemas se vieron afectados (Articulo 17-19)', en: 'Cannot demonstrate which systems were affected (Articles 17-19)' },
          solution: { es: 'Incidencias nativamente vinculadas a activos — evaluacion de impacto basada en datos reales', en: 'Incidents natively linked to assets — impact assessment based on real asset data' },
        },
        {
          gap: { es: 'Sin visibilidad de proveedores', en: 'No vendor visibility' },
          risk: { es: 'No puede gestionar el riesgo de terceros TIC (Articulo 28)', en: 'Cannot manage ICT third-party risk (Article 28)' },
          solution: { es: 'Registro de proveedores con trazabilidad activo-proveedor', en: 'Vendor registry with asset-to-vendor traceability' },
        },
        {
          gap: { es: 'Respuesta manual a vulnerabilidades', en: 'Manual vulnerability response' },
          risk: { es: 'Dias para evaluar la exposicion, no puede cumplir plazos del Art. 19 (4h/72h)', en: 'Days to assess exposure, cannot meet Article 19 timelines (4h/72h)' },
          solution: { es: 'Busqueda instantanea por fabricante, modelo, firmware — dispositivos afectados en segundos', en: 'Instant search by manufacturer, model, firmware — affected devices in seconds' },
        },
        {
          gap: { es: 'Sin audit trail', en: 'No audit trail' },
          risk: { es: 'No puede demostrar cumplimiento ante el supervisor', en: 'Cannot demonstrate compliance to supervisors' },
          solution: { es: 'Cada accion sobre cada activo registrada con usuario, timestamp y detalles', en: 'Every action on every asset logged with user, timestamp, and details' },
        },
      ],
    },
    timeline: {
      title: { es: 'Timeline DORA', en: 'DORA Timeline' },
      items: [
        { date: 'Ene 2023', event: { es: 'DORA entra en vigor', en: 'DORA enters into force' } },
        { date: 'Ene 2025', event: { es: 'DORA es aplicable. Las entidades financieras deben cumplir. Las inspecciones pueden comenzar.', en: 'DORA becomes applicable. Financial entities must comply. Supervisory inspections can begin.' } },
        { date: 'Mar 2026', event: { es: 'DSM Control disponible — capacidad inmediata de cumplimiento del Articulo 8', en: 'DSM Control available — immediate Article 8 compliance capability' } },
        { date: '2026-2027', event: { es: 'Primera ola de revisiones supervisoras DORA. El inventario de activos es lo primero que comprueban.', en: 'First wave of DORA supervisory reviews. Asset inventory is the first thing they check.' } },
      ],
    },
    summary: {
      title: { es: 'Conclusion', en: 'Summary' },
      text: {
        es: 'DORA convierte la gestion de activos TIC en un requisito regulatorio para todo el sector financiero europeo. El mandato del Articulo 8 de "identificar, clasificar y documentar adecuadamente todos los activos TIC" no es opcional — es la base de todo el marco de compliance DORA. DSM Control proporciona la capa de implementacion: identificar (inventario completo), clasificar (criticidad y funcion de negocio), documentar (ciclo de vida completo), monitorizar (mantenimiento y estado), responder (incidencias vinculadas a activos) y demostrar (audit trail). DORA es aplicable desde enero de 2025. Cada dia sin una gestion adecuada de activos TIC es un dia de exposicion regulatoria.',
        en: 'DORA makes ICT asset management a regulatory requirement for the entire EU financial sector. Article 8\'s mandate to "identify, classify and adequately document all ICT assets" is not optional — it\'s the foundation of the entire DORA compliance framework. DSM Control provides the implementation layer: identify (complete inventory), classify (criticality and business function), document (full lifecycle), monitor (maintenance and status), respond (asset-linked incidents), and prove (audit trail). DORA has been applicable since January 2025. Every day without proper ICT asset management is a day of regulatory exposure.',
      },
    },
  },
];
