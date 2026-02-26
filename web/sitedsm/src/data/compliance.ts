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
      es: 'Por que necesitas DSM Control para cumplir NIS2',
      en: 'Why you need DSM Control for NIS2 compliance',
    },
    subtitle: {
      es: 'NIS2 exige a las empresas europeas documentar y controlar sus activos TIC. DSM Control cubre los requisitos de gestion de activos, incidencias y trazabilidad que exige la directiva.',
      en: 'NIS2 requires European organizations to document and control their IT assets. DSM Control covers the asset management, incident handling, and traceability requirements mandated by the directive.',
    },
    what: {
      title: { es: 'Que es NIS2', en: 'What is NIS2' },
      text: {
        es: 'NIS2 es la directiva europea de ciberseguridad que sustituye a la NIS original (2016). Amplia significativamente el numero de organizaciones afectadas, introduce requisitos mas estrictos y anade responsabilidad personal para la direccion. Es exigible desde octubre de 2024 y afecta a entidades esenciales e importantes en 18 sectores: energia, transporte, sanidad, manufactura, alimentacion, servicios financieros, infraestructura digital y mas.',
        en: 'NIS2 is the EU cybersecurity directive replacing the original NIS Directive (2016). It significantly expands the number of organizations in scope, introduces stricter requirements, and adds personal liability for management. It has been enforceable since October 2024 and affects essential and important entities across 18 sectors: energy, transport, health, manufacturing, food, financial services, digital infrastructure, and more.',
      },
    },
    who: {
      title: { es: 'Quien debe cumplir', en: 'Who must comply' },
      items: [
        {
          es: 'Entidades esenciales: grandes organizaciones en sectores criticos (energia, transporte, sanidad, banca, agua, infraestructura digital)',
          en: 'Essential entities: large organizations in critical sectors (energy, transport, health, banking, water, digital infrastructure)',
        },
        {
          es: 'Entidades importantes: organizaciones medianas (50+ empleados o 10M+ facturacion) en los mismos sectores mas manufactura, alimentacion, quimica, servicios postales',
          en: 'Important entities: medium organizations (50+ employees or €10M+ revenue) in the same sectors plus manufacturing, food, chemicals, postal services',
        },
        {
          es: 'Cadena de suministro: cualquier empresa que provea servicios o productos TIC a entidades esenciales/importantes, independientemente de su tamano',
          en: 'Supply chain: any company providing ICT services or products to essential/important entities, regardless of size',
        },
      ],
    },
    penalties: {
      title: { es: 'Sanciones', en: 'Penalties' },
      items: [
        { es: 'Entidades esenciales: hasta 10M EUR o 2% de la facturacion global anual', en: 'Essential entities: up to €10M or 2% of global annual turnover' },
        { es: 'Entidades importantes: hasta 7M EUR o 1,4% de la facturacion global anual', en: 'Important entities: up to €7M or 1.4% of global annual turnover' },
        { es: 'Responsabilidad personal: los organos de direccion pueden ser personalmente responsables del incumplimiento', en: 'Personal liability: management bodies can be held personally liable for non-compliance' },
      ],
    },
    mappings: {
      title: { es: 'Requisitos NIS2 mapeados a DSM Control', en: 'NIS2 requirements mapped to DSM Control' },
      subtitle: {
        es: 'El Articulo 21 es el nucleo de NIS2. Exige medidas tecnicas, operativas y organizativas para gestionar los riesgos de seguridad. Asi cubre DSM Control cada requisito:',
        en: 'Article 21 is the core of NIS2. It requires technical, operational, and organizational measures to manage security risks. Here is how DSM Control covers each requirement:',
      },
      items: [
        {
          requirement: { es: 'Art. 21(a) — Politicas de analisis de riesgos', en: 'Art. 21(a) — Risk analysis policies' },
          meaning: { es: 'Documentar que sistemas tienes y su exposicion al riesgo', en: 'Document what systems you have and their risk exposure' },
          feature: { es: 'Inventario de activos con clasificacion', en: 'Asset inventory with classification' },
          how: { es: 'Cada dispositivo registrado con tipo, fabricante, modelo, numero de serie y clasificacion de riesgo. Registro de activos exportable como base para el analisis de riesgos.', en: 'Every device registered with type, manufacturer, model, serial number, and risk classification. Exportable asset register as the foundation for risk analysis.' },
        },
        {
          requirement: { es: 'Art. 21(b) — Gestion de incidencias', en: 'Art. 21(b) — Incident handling' },
          meaning: { es: 'Detectar, reportar y responder a incidencias con procedimientos documentados', en: 'Detect, report, and respond to incidents with documented procedures' },
          feature: { es: 'Gestion de incidencias vinculadas a activos', en: 'Incident management with asset-linked tickets' },
          how: { es: 'Cada incidencia se crea contra un activo especifico. La timeline muestra que paso, cuando y que acciones se tomaron. Las incidencias no pueden existir sin estar vinculadas a un dispositivo — por diseno.', en: 'Every incident is created against a specific asset. Timeline shows what happened, when, and what actions were taken. Incidents cannot exist without being linked to a device — by design.' },
        },
        {
          requirement: { es: 'Art. 21(c) — Continuidad de negocio', en: 'Art. 21(c) — Business continuity' },
          meaning: { es: 'Saber que activos son criticos y planificar ante su fallo', en: 'Know what assets are critical and plan for failure' },
          feature: { es: 'Clasificacion de criticidad + planes de mantenimiento', en: 'Criticality classification + maintenance plans' },
          how: { es: 'Los activos se clasifican por criticidad. Los planes de mantenimiento preventivo aseguran que los dispositivos criticos se mantienen proactivamente. El historial de incidencias por activo revela que dispositivos son un riesgo.', en: 'Assets classified by criticality. Preventive maintenance schedules ensure critical devices are proactively maintained. Incident history per asset reveals reliability risks.' },
        },
        {
          requirement: { es: 'Art. 21(d) — Seguridad de la cadena de suministro', en: 'Art. 21(d) — Supply chain security' },
          meaning: { es: 'Saber que hardware y software despliegas y de quien', en: 'Know what hardware and software you deploy and from whom' },
          feature: { es: 'Ordenes de compra con seguimiento de proveedores', en: 'Purchase orders with vendor tracking' },
          how: { es: 'Cada activo es trazable a una orden de compra, un proveedor y una fecha de entrega. El registro de proveedores da una vision completa de la cadena de suministro TIC.', en: 'Every asset traceable to a purchase order, vendor, and delivery date. Vendor registry provides complete ICT supply chain visibility.' },
        },
        {
          requirement: { es: 'Art. 21(e) — Seguridad en la adquisicion y mantenimiento de sistemas', en: 'Art. 21(e) — Security in acquisition and maintenance' },
          meaning: { es: 'Seguimiento de dispositivos durante todo su ciclo de vida', en: 'Track devices through their entire lifecycle' },
          feature: { es: 'Gestion completa del ciclo de vida', en: 'Full lifecycle management' },
          how: { es: 'DSM Control gestiona el ciclo de vida completo: compra, almacen, asignacion, incidencias, mantenimiento y baja. Cada etapa esta documentada con timestamps, responsables y audit trail.', en: 'DSM Control manages the complete lifecycle: purchase, warehouse, assignment, incidents, maintenance, and decommission. Every stage documented with timestamps, owners, and audit trail.' },
        },
        {
          requirement: { es: 'Art. 21(f) — Evaluacion de la eficacia de las medidas', en: 'Art. 21(f) — Assessing effectiveness of measures' },
          meaning: { es: 'Medir si tus controles funcionan', en: 'Measure whether your controls work' },
          feature: { es: 'Dashboard en tiempo real + audit trail', en: 'Real-time dashboard + audit trail' },
          how: { es: 'Dashboard con incidencias abiertas, cumplimiento SLA, distribucion de estados de activos y adherencia al mantenimiento. Audit trail documenta cada accion sobre cada activo.', en: 'Dashboard with open incidents, SLA compliance, asset status distribution, and maintenance adherence. Audit trail documents every action on every asset.' },
        },
        {
          requirement: { es: 'Art. 21(i) — Gestion de activos', en: 'Art. 21(i) — Asset management' },
          meaning: { es: 'Mencionado explicitamente: la gestion de activos es una medida obligatoria', en: 'Explicitly mentioned: asset management is a required measure' },
          feature: { es: 'Funcionalidad principal del producto', en: 'Core product functionality' },
          how: { es: 'DSM Control esta construido especificamente para la gestion de activos TIC. Inventario, seguimiento de asignaciones y permisos basados en roles son capacidades nativas.', en: 'DSM Control is purpose-built for IT asset management. Inventory, assignment tracking, and role-based permissions are native capabilities.' },
        },
      ],
    },
    auditor: {
      title: { es: 'Las 3 preguntas que hara tu auditor NIS2', en: 'The 3 questions your NIS2 auditor will ask' },
      questions: [
        {
          question: { es: 'Que dispositivos tiene tu empresa en su red?', en: 'What devices does your organization have on its network?' },
          without: { es: 'Hoja de calculo, desactualizada, incompleta, sin fuente unica de verdad', en: 'Spreadsheet, outdated, incomplete, no single source of truth' },
          with: { es: 'Inventario completo de activos con estado, ubicacion y responsable — siempre actualizado', en: 'Complete asset inventory with status, location, and responsible person — always current' },
        },
        {
          question: { es: 'Quien tiene acceso a que dispositivos?', en: 'Who has access to which devices?' },
          without: { es: '"Dejame preguntar a RRHH" o "Creo que Maria tiene ese portatil"', en: '"Let me check with HR" or "I think Maria has that laptop"' },
          with: { es: 'Historial de asignaciones con trazabilidad temporal — quien tuvo que, cuando, y cada cambio documentado', en: 'Assignment history with temporal traceability — who had what, when, and every change documented' },
        },
        {
          question: { es: 'Que incidencias han tenido esos dispositivos?', en: 'What incidents have those devices had?' },
          without: { es: '"Teniamos tickets en el helpdesk pero no estan vinculados a dispositivos especificos"', en: '"We had tickets in the helpdesk but they are not linked to specific devices"' },
          with: { es: 'Cada incidencia vinculada al activo especifico, con timeline completa, acciones tomadas y resolucion — exportable', en: 'Every incident linked to the specific asset, with full timeline, actions taken, and resolution — exportable' },
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
          solution: { es: 'Incidencias nativamente vinculadas a activos — sin integracion necesaria', en: 'Incidents natively linked to assets — no integration needed' },
        },
        {
          gap: { es: 'Sin trazabilidad compra-a-baja', en: 'No purchase-to-decommission traceability' },
          risk: { es: 'No puede demostrar seguridad de la cadena de suministro (Art. 21(d))', en: 'Cannot demonstrate supply chain security (Article 21(d))' },
          solution: { es: 'Ciclo de vida completo desde orden de compra hasta baja con seguimiento de proveedores', en: 'Full lifecycle from purchase order to decommission with vendor tracking' },
        },
        {
          gap: { es: 'Sin audit trail', en: 'No audit trail' },
          risk: { es: 'No puede demostrar que acciones se tomaron y por quien', en: 'Cannot prove what actions were taken and by whom' },
          solution: { es: 'Cada accion sobre cada activo registrada con usuario, timestamp y detalles', en: 'Every action on every asset logged with user, timestamp, and details' },
        },
        {
          gap: { es: 'Gaps en offboarding — dispositivos no recuperados', en: 'Offboarding gaps — devices not recovered' },
          risk: { es: 'Activos sin control en manos de exempleados', en: 'Uncontrolled assets in the field' },
          solution: { es: 'Gestion de asignaciones con workflows de offboarding y seguimiento de recuperacion', en: 'Assignment management with offboarding workflows and recovery tracking' },
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
        { date: '2025', event: { es: 'Primeros ciclos de auditoria. Empresas empiezan a recibir requerimientos.', en: 'First audit cycles. Companies start receiving requirements.' } },
        { date: 'Mar 2026', event: { es: 'DSM Control disponible — preparado para NIS2 desde el dia 1', en: 'DSM Control available — NIS2 ready from day one' } },
        { date: 'Sep 2026', event: { es: 'Presion de compliance aumenta. Las empresas necesitan documentacion AHORA.', en: 'Compliance pressure increases. Companies need documentation NOW.' } },
        { date: '2027+', event: { es: 'Enforcement pleno. NIS2 + DORA + CRA activos simultaneamente.', en: 'Full enforcement. NIS2 + DORA + CRA all active simultaneously.' } },
      ],
    },
    summary: {
      title: { es: 'Conclusion', en: 'Summary' },
      text: {
        es: 'DSM Control no es una herramienta generica de ciberseguridad. Esta construido especificamente para los requisitos que NIS2 Articulo 21(i) exige explicitamente: gestion de activos. Proporciona la trazabilidad documentada, auditable y a nivel de dispositivo que NIS2 requiere — vinculando cada dispositivo a su ciclo de vida, cada incidencia a su dispositivo, y cada accion a su audit trail. Para PYMEs que entran en el ambito NIS2 por primera vez, DSM Control reemplaza la hoja de calculo con un sistema preparado para compliance — sin el coste ni la complejidad de herramientas enterprise.',
        en: 'DSM Control is not a generic cybersecurity tool. It is purpose-built for the specific requirements that NIS2 Article 21(i) explicitly mandates: asset management. It provides the documented, auditable, device-level traceability that NIS2 requires — linking every device to its lifecycle, every incident to its device, and every action to its audit trail. For SMBs entering NIS2 scope for the first time, DSM Control replaces the spreadsheet with a compliance-ready system — without the cost or complexity of enterprise tools.',
      },
    },
  },

  // ─── ISO 27001 ───────────────────────────────────────
  {
    slug: 'iso27001',
    badge: { es: 'ISO/IEC 27001:2022', en: 'ISO/IEC 27001:2022' },
    headline: {
      es: 'Por que necesitas DSM Control para certificarte en ISO 27001',
      en: 'Why you need DSM Control for ISO 27001 certification',
    },
    subtitle: {
      es: 'ISO 27001 exige controles de gestion de activos, incidencias, mantenimiento y baja segura. DSM Control cubre directamente 12 controles del Anexo A y soporta 8 mas — el 21,5% de los 93 controles totales.',
      en: 'ISO 27001 requires controls for asset management, incidents, maintenance, and secure disposal. DSM Control directly addresses 12 Annex A controls and supports 8 more — 21.5% of all 93 controls.',
    },
    what: {
      title: { es: 'Que es ISO 27001', en: 'What is ISO 27001' },
      text: {
        es: 'ISO 27001 es el estandar internacional para Sistemas de Gestion de Seguridad de la Informacion (SGSI). A diferencia de NIS2 o CRA, es voluntario — pero cada vez mas exigido por clientes, partners, reguladores y aseguradoras como prueba de madurez en seguridad. Muchas organizaciones afectadas por NIS2 persiguen la certificacion ISO 27001 como marco estructurado para demostrar cumplimiento. La Comision Europea referencia explicitamente ISO 27001 como framework reconocido para NIS2.',
        en: 'ISO 27001 is the international standard for Information Security Management Systems (ISMS). Unlike NIS2 or CRA, it is voluntary — but increasingly required by clients, partners, regulators, and insurers as proof of security maturity. Many NIS2-affected organizations pursue ISO 27001 certification as a structured framework to demonstrate compliance. The European Commission explicitly references ISO 27001 as a recognized framework for NIS2.',
      },
    },
    who: {
      title: { es: 'Por que importa para tu empresa', en: 'Why it matters for your company' },
      items: [
        { es: 'Clientes B2B exigen ISO 27001 antes de firmar contratos', en: 'B2B clients require ISO 27001 before signing contracts' },
        { es: 'Las polizas de ciberseguro referencian ISO 27001 como requisito base', en: 'Cyber insurance policies reference ISO 27001 as a baseline requirement' },
        { es: 'NIS2 + ISO 27001 se complementan: las organizaciones usan ISO 27001 para implementar los requisitos NIS2', en: 'NIS2 + ISO 27001 complement each other: organizations use ISO 27001 to implement NIS2 requirements' },
        { es: 'Ventaja competitiva: la certificacion diferencia a PYMEs de competidores que no pueden demostrar practicas de seguridad', en: 'Competitive advantage: certification differentiates SMBs from competitors who cannot demonstrate security practices' },
      ],
    },
    penalties: {
      title: { es: 'Consecuencias del incumplimiento', en: 'Consequences of non-compliance' },
      items: [
        { es: 'Perdida de certificacion en auditorias de vigilancia (cada ano)', en: 'Loss of certification in surveillance audits (every year)' },
        { es: 'Perdida de contratos con clientes que exigen ISO 27001', en: 'Loss of contracts with clients that require ISO 27001' },
        { es: 'No-conformidades en controles de activos son de las mas citadas por auditores', en: 'Non-conformities in asset controls are among the most cited by auditors' },
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
          how: { es: 'Inventario con propietario (usuario asignado), ubicacion, estado y metadatos. Este es el control mas importante para la propuesta de valor de DSM Control.', en: 'Inventory with owner (assigned user), location, status, and metadata. This is the single most important control for DSM Control\'s value proposition.' },
        },
        {
          requirement: { es: 'A.5.11 — Devolucion de activos', en: 'A.5.11 — Return of assets' },
          meaning: { es: 'El personal debe devolver todos los activos al terminar su relacion laboral', en: 'Personnel shall return all assets upon termination of employment' },
          feature: { es: 'Gestion de asignaciones con offboarding', en: 'Assignment management with offboarding' },
          how: { es: 'Cuando un empleado se va, DSM Control muestra exactamente que dispositivos tiene. La recuperacion se puede rastrear y verificar.', en: 'When an employee leaves, DSM Control shows exactly what devices they have. Recovery can be tracked and verified.' },
        },
        {
          requirement: { es: 'A.5.24–A.5.28 — Gestion de incidencias de seguridad', en: 'A.5.24–A.5.28 — Security incident management' },
          meaning: { es: 'Planificacion, evaluacion, respuesta, aprendizaje y recopilacion de evidencias de incidencias', en: 'Planning, assessment, response, learning, and evidence collection for incidents' },
          feature: { es: 'Gestion de incidencias con vinculacion a activos', en: 'Incident management with asset linking' },
          how: { es: 'Workflow completo de incidencias: creacion contra activo, clasificacion, asignacion, resolucion. Timeline con timestamps. Historial por activo revela patrones. Audit trail preserva evidencias.', en: 'Complete incident workflow: creation against asset, classification, assignment, resolution. Timeline with timestamps. History per asset reveals patterns. Audit trail preserves evidence.' },
        },
        {
          requirement: { es: 'A.7.9 — Seguridad de activos fuera de las instalaciones', en: 'A.7.9 — Security of assets off-premises' },
          meaning: { es: 'Los activos fuera de las instalaciones deben estar protegidos', en: 'Off-site assets shall be protected' },
          feature: { es: 'Seguimiento de asignaciones y envios', en: 'Assignment and shipment tracking' },
          how: { es: 'Seguimiento de que dispositivos estan fuera (empleados remotos, otras sedes). Modulo de envios con cadena de custodia.', en: 'Track which devices are off-site (remote employees, other locations). Shipment module with chain of custody.' },
        },
        {
          requirement: { es: 'A.7.13 — Mantenimiento de equipos', en: 'A.7.13 — Equipment maintenance' },
          meaning: { es: 'Los equipos deben mantenerse correctamente para asegurar su disponibilidad', en: 'Equipment shall be maintained correctly to ensure availability' },
          feature: { es: 'Mantenimiento preventivo y correctivo', en: 'Preventive and corrective maintenance' },
          how: { es: 'Modulo de mantenimiento con calendario, programacion y seguimiento de finalizacion. Historial de mantenimiento por activo como registro auditable.', en: 'Maintenance module with calendar, scheduling, and completion tracking. Maintenance history per asset as auditable record.' },
        },
        {
          requirement: { es: 'A.7.14 — Baja segura o reutilizacion de equipos', en: 'A.7.14 — Secure disposal or re-use of equipment' },
          meaning: { es: 'Verificar que los datos se han eliminado antes de la baja o reutilizacion', en: 'Verify data has been removed prior to disposal or re-use' },
          feature: { es: 'Etapa de baja en el ciclo de vida', en: 'Decommission lifecycle stage' },
          how: { es: 'La etapa de baja documenta cuando y como se retiro un dispositivo. Campos personalizados para metodo de sanitizacion y certificado de destruccion.', en: 'Decommission stage documents when and how a device was retired. Custom fields for sanitization method and destruction certificate.' },
        },
        {
          requirement: { es: 'A.8.1 — Dispositivos de usuario final', en: 'A.8.1 — User endpoint devices' },
          meaning: { es: 'Proteger la informacion en dispositivos de usuario', en: 'Protect information on user endpoint devices' },
          feature: { es: 'Inventario de endpoints', en: 'Endpoint inventory' },
          how: { es: 'Inventario completo de todos los endpoints (portatiles, telefonos, tablets) con usuario asignado, ubicacion e historial de incidencias.', en: 'Complete inventory of all endpoints (laptops, phones, tablets) with assigned user, location, and incident history.' },
        },
      ],
    },
    auditor: {
      title: { es: 'Que necesita ver el auditor ISO 27001', en: 'What the ISO 27001 auditor needs to see' },
      questions: [
        {
          question: { es: 'Muestrame tu inventario de activos', en: 'Show me your asset inventory' },
          without: { es: 'Archivo Excel, posiblemente desactualizado, sin seguimiento de propietarios', en: 'Excel file, possibly outdated, no owner tracking' },
          with: { es: 'Inventario en vivo con propietarios, ubicaciones y estado — siempre actualizado', en: 'Live inventory with owners, locations, and status — always current' },
        },
        {
          question: { es: 'Como verificais que los activos se devuelven cuando un empleado se va?', en: 'How do you verify assets are returned when employees leave?' },
          without: { es: 'Proceso manual por email, sin verificacion', en: 'Manual email process, no verification' },
          with: { es: 'Workflow de offboarding con lista de dispositivos por empleado y confirmacion de recuperacion', en: 'Offboarding workflow with device list per employee and recovery confirmation' },
        },
        {
          question: { es: 'Muestrame los registros de mantenimiento de los equipos criticos', en: 'Show me maintenance records for critical equipment' },
          without: { es: 'Registros en papel o emails sueltos', en: 'Paper records or ad-hoc emails' },
          with: { es: 'Modulo de mantenimiento con tareas programadas y completadas por activo', en: 'Maintenance module with scheduled and completed tasks per asset' },
        },
        {
          question: { es: 'Muestrame el audit trail', en: 'Show me your audit trail' },
          without: { es: 'No existe', en: 'Does not exist' },
          with: { es: 'Cada accion sobre cada activo registrada con usuario, timestamp y detalles', en: 'Every action on every asset logged with user, timestamp, and details' },
        },
      ],
    },
    gaps: {
      title: { es: 'No-conformidades habituales que DSM Control evita', en: 'Common non-conformities that DSM Control prevents' },
      items: [
        {
          gap: { es: 'Inventario no mantenido (A.5.9)', en: 'Inventory not maintained (A.5.9)' },
          risk: { es: 'No-conformidad mayor — el control mas auditado', en: 'Major non-conformity — the most audited control' },
          solution: { es: 'Sistema que impone el registro y rastrea cambios automaticamente', en: 'System that enforces registration and tracks changes automatically' },
        },
        {
          gap: { es: 'Sin proceso de devolucion verificable (A.5.11)', en: 'No verifiable return process (A.5.11)' },
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
      title: { es: 'Conclusion', en: 'Summary' },
      text: {
        es: 'ISO 27001 es el estandar de seguridad de la informacion mas adoptado del mundo. Para organizaciones que buscan la certificacion — especialmente PYMEs — los controles de gestion de activos e incidencias (A.5.9, A.5.11, A.5.24–A.5.28, A.7.13, A.7.14, A.8.1) estan entre los mas auditados y los que mas no-conformidades generan. DSM Control cubre directamente 12 controles del Anexo A y soporta 8 mas. Para empresas que tambien estan afectadas por NIS2, DSM Control proporciona una unica plataforma que satisface ambos frameworks simultaneamente. DSM Control es la columna vertebral de gestion de activos de tu SGSI.',
        en: 'ISO 27001 is the most widely adopted information security standard in the world. For organizations pursuing certification — especially SMBs — asset management and incident controls (A.5.9, A.5.11, A.5.24–A.5.28, A.7.13, A.7.14, A.8.1) are among the most audited and most frequently cited as non-conformities. DSM Control directly addresses 12 Annex A controls and supports 8 more. For companies also affected by NIS2, DSM Control provides a single platform that satisfies both frameworks simultaneously. DSM Control is the asset management backbone of your ISMS.',
      },
    },
  },

  // ─── CRA ─────────────────────────────────────────────
  {
    slug: 'cra',
    badge: { es: 'Reglamento (UE) 2024/2847', en: 'Regulation (EU) 2024/2847' },
    headline: {
      es: 'Por que necesitas DSM Control para cumplir el CRA',
      en: 'Why you need DSM Control for CRA compliance',
    },
    subtitle: {
      es: 'El Cyber Resilience Act obliga a los fabricantes a divulgar vulnerabilidades. Las empresas que usan esos productos necesitan responder en minutos, no en dias. DSM Control te dice en 30 segundos si estas afectado.',
      en: 'The Cyber Resilience Act requires manufacturers to disclose vulnerabilities. Companies using those products need to respond in minutes, not days. DSM Control tells you in 30 seconds if you are affected.',
    },
    what: {
      title: { es: 'Que es el CRA', en: 'What is the CRA' },
      text: {
        es: 'El Cyber Resilience Act (CRA) es un reglamento de la UE que establece requisitos de ciberseguridad para productos con elementos digitales — cualquier hardware o software que se conecte a una red. A diferencia de NIS2 (que afecta a las organizaciones que usan tecnologia), el CRA afecta a las que fabrican, importan o distribuyen productos tecnologicos. Las obligaciones de reporte empiezan en septiembre de 2026 y el cumplimiento total se exige en diciembre de 2027.',
        en: 'The Cyber Resilience Act (CRA) is an EU regulation establishing cybersecurity requirements for products with digital elements — any hardware or software that connects to a network. Unlike NIS2 (which targets organizations that use technology), the CRA targets those that manufacture, import, or distribute technology products. Reporting obligations start September 2026 and full compliance is required by December 2027.',
      },
    },
    who: {
      title: { es: 'A quien afecta', en: 'Who is affected' },
      items: [
        { es: 'Fabricantes de productos con elementos digitales (hardware con software embebido, software, dispositivos IoT)', en: 'Manufacturers of products with digital elements (hardware with embedded software, software, IoT devices)' },
        { es: 'Importadores que colocan productos de fuera de la UE en el mercado europeo', en: 'Importers placing products from outside the EU on the European market' },
        { es: 'Distribuidores que hacen disponibles productos en el mercado de la UE', en: 'Distributors making products available on the EU market' },
        { es: 'Cualquier empresa que USE productos con elementos digitales — porque recibira notificaciones de vulnerabilidades de los fabricantes', en: 'Any company that USES products with digital elements — because they will receive vulnerability notifications from manufacturers' },
      ],
    },
    penalties: {
      title: { es: 'Sanciones', en: 'Penalties' },
      items: [
        { es: 'Hasta 15M EUR o 2,5% de la facturacion global anual por incumplimiento de requisitos esenciales', en: 'Up to €15M or 2.5% of global annual turnover for non-compliance with essential requirements' },
        { es: 'Hasta 10M EUR o 2% por otras infracciones', en: 'Up to €10M or 2% for other violations' },
        { es: 'Hasta 5M EUR o 1% por proporcionar informacion incorrecta', en: 'Up to €5M or 1% for providing incorrect information' },
      ],
    },
    mappings: {
      title: { es: 'Impacto del CRA y como responde DSM Control', en: 'CRA impact and how DSM Control responds' },
      subtitle: {
        es: 'El CRA crea una nueva realidad: los fabricantes divulgaran vulnerabilidades y tu empresa necesita responder. Estos son los escenarios criticos:',
        en: 'The CRA creates a new reality: manufacturers will disclose vulnerabilities and your company needs to respond. These are the critical scenarios:',
      },
      items: [
        {
          requirement: { es: 'Un fabricante divulga una vulnerabilidad', en: 'A manufacturer discloses a vulnerability' },
          meaning: { es: '"Hay una vulnerabilidad critica en los routers TapLink RX-500. ¿Tenemos alguno? ¿Donde?"', en: '"There is a critical vulnerability in TapLink RX-500 routers. Do we have any? Where?"' },
          feature: { es: 'Busqueda por fabricante y modelo', en: 'Search by manufacturer and model' },
          how: { es: 'Filtra por fabricante + modelo. En 30 segundos: cuantas unidades, donde estan, quien las tiene. Crea incidencias para todos los dispositivos afectados inmediatamente.', en: 'Filter by manufacturer + model. In 30 seconds: how many units, where they are, who has them. Create incidents for all affected devices immediately.' },
        },
        {
          requirement: { es: 'Un fabricante publica una actualizacion de firmware', en: 'A manufacturer issues a firmware update' },
          meaning: { es: 'Necesitas identificar todos los dispositivos afectados y aplicar la actualizacion', en: 'You need to identify all affected devices and apply the update' },
          feature: { es: 'Tareas de mantenimiento vinculadas a activos', en: 'Maintenance tasks linked to assets' },
          how: { es: 'Filtra dispositivos afectados, crea tarea de mantenimiento, rastrea estado de actualizacion por dispositivo. Dashboard muestra porcentaje de completado.', en: 'Filter affected devices, create maintenance task, track update status per device. Dashboard shows completion percentage.' },
        },
        {
          requirement: { es: 'Un fabricante retira un producto del mercado', en: 'A manufacturer recalls a product' },
          meaning: { es: 'Necesitas identificar y retirar del servicio todas las unidades', en: 'You need to identify and remove all units from service' },
          feature: { es: 'Workflow de baja con trazabilidad', en: 'Decommission workflow with traceability' },
          how: { es: 'Lista inmediata de dispositivos con ubicaciones y usuarios asignados. Workflow de baja para cada unidad. Audit trail completo del proceso de retirada.', en: 'Immediate device list with locations and assigned users. Decommission workflow for each unit. Full audit trail of the recall process.' },
        },
        {
          requirement: { es: 'Un auditor pregunta como respondiste a una divulgacion CRA', en: 'An auditor asks how you responded to a CRA disclosure' },
          meaning: { es: '"Cuando se publico el aviso de vulnerabilidad del producto X en octubre, ¿como respondio tu organizacion?"', en: '"When the vulnerability advisory for product X was published in October, how did your organization respond?"' },
          feature: { es: 'Timeline de incidencias con evidencia', en: 'Incident timeline with evidence' },
          how: { es: 'Incidencia creada el 3 de octubre a las 09:14. Vinculada a 8 dispositivos. Firmware actualizado en los 8 para el 5 de octubre. Timeline exportable con cada paso documentado.', en: 'Incident created October 3rd at 09:14. Linked to 8 devices. Firmware updated on all 8 by October 5th. Exportable timeline with every step documented.' },
        },
      ],
    },
    auditor: {
      title: { es: 'La pregunta que no podras responder sin DSM Control', en: 'The question you cannot answer without DSM Control' },
      questions: [
        {
          question: { es: 'Cuantos dispositivos del modelo X tenemos?', en: 'How many devices of model X do we have?' },
          without: { es: 'Llamadas a cada oficina, revisar ordenes de compra en emails, dias de investigacion', en: 'Phone calls to each office, checking purchase orders in email, days of investigation' },
          with: { es: 'Filtro por fabricante + modelo. Resultado en 30 segundos con ubicaciones y usuarios', en: 'Filter by manufacturer + model. Result in 30 seconds with locations and users' },
        },
        {
          question: { es: 'Cuales de nuestros routers tienen el firmware 4.2.1 vulnerable?', en: 'Which of our routers are running vulnerable firmware 4.2.1?' },
          without: { es: 'Imposible saberlo sin revisar fisicamente cada router', en: 'Impossible to know without physically checking each router' },
          with: { es: 'Campo personalizado "version_firmware" filtrado a "4.2.1". Resultado: 5 dispositivos identificados', en: 'Custom field "firmware_version" filtered to "4.2.1". Result: 5 devices identified' },
        },
        {
          question: { es: 'Que hicimos cuando el fabricante publico el aviso de seguridad?', en: 'What did we do when the manufacturer published the security advisory?' },
          without: { es: 'Sin evidencia documentada de la respuesta', en: 'No documented evidence of response' },
          with: { es: 'Incidencia con timeline completa: deteccion, dispositivos afectados, acciones tomadas, resolucion. Todo exportable.', en: 'Incident with full timeline: detection, affected devices, actions taken, resolution. All exportable.' },
        },
      ],
    },
    gaps: {
      title: { es: 'Gaps criticos que el CRA expone', en: 'Critical gaps that the CRA exposes' },
      items: [
        {
          gap: { es: 'Sin inventario por fabricante y modelo', en: 'No inventory by manufacturer and model' },
          risk: { es: 'No puedes responder a divulgaciones de vulnerabilidades del CRA', en: 'Cannot respond to CRA vulnerability disclosures' },
          solution: { es: 'Inventario con fabricante, modelo, numero de serie y version de firmware por dispositivo', en: 'Inventory with manufacturer, model, serial number, and firmware version per device' },
        },
        {
          gap: { es: 'Sin capacidad de respuesta rapida', en: 'No rapid response capability' },
          risk: { es: 'Dias o semanas para evaluar exposicion a una vulnerabilidad', en: 'Days or weeks to assess exposure to a vulnerability' },
          solution: { es: 'Busqueda instantanea + creacion masiva de incidencias para dispositivos afectados', en: 'Instant search + bulk incident creation for affected devices' },
        },
        {
          gap: { es: 'Sin evidencia de respuesta a incidentes', en: 'No evidence of incident response' },
          risk: { es: 'No puede demostrar al auditor NIS2 como respondio a las divulgaciones CRA', en: 'Cannot demonstrate to NIS2 auditor how it responded to CRA disclosures' },
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
      title: { es: 'Conclusion', en: 'Summary' },
      text: {
        es: 'El CRA crea una nueva realidad: los fabricantes estaran obligados a divulgar vulnerabilidades, y las organizaciones que usen esos productos necesitaran responder rapidamente y documentar su respuesta. Esto transforma la gestion de activos TIC de un "esta bien tenerlo" a una capacidad critica para el compliance. DSM Control proporciona la capa esencial que conecta las divulgaciones CRA con los dispositivos reales de tu organizacion: saber que tienes, donde esta, responder rapido y demostrar que respondiste. Las obligaciones de reporte CRA empiezan en septiembre de 2026. El momento de prepararse es ahora.',
        en: 'The CRA creates a new reality: manufacturers will be required to disclose vulnerabilities, and organizations using those products will need to respond rapidly and document their response. This transforms IT asset management from a "nice to have" into a compliance-critical capability. DSM Control provides the essential layer connecting CRA disclosures to actual devices in your organization: know what you have, where it is, respond fast, and prove you responded. CRA reporting obligations start September 2026. The time to prepare is now.',
      },
    },
  },
];
