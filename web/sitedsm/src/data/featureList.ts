import type { Lang } from '../i18n/translations';

export interface Feature {
  name: Record<Lang, string>;
  desc: Record<Lang, string>;
}

export interface FeatureCategory {
  id: string;
  name: Record<Lang, string>;
  icon: string;
  features: Feature[];
}

const s = (es: string, en: string) => ({ es, en });

export const featureCategories: FeatureCategory[] = [
  {
    id: 'asset-management',
    name: s('Gestion de activos', 'Asset Management'),
    icon: 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4',
    features: [
      {
        name: s('Inventario de activos', 'Asset inventory'),
        desc: s(
          'Todos tus dispositivos en un solo lugar — portatiles, monitores, telefonos, servidores. Busqueda, filtros y exportacion CSV.',
          'All your devices in one place — laptops, monitors, phones, servers. Search, filters, and CSV export.'
        ),

      },
      {
        name: s('Tipos, estados y numeros de serie', 'Types, statuses, and serial numbers'),
        desc: s(
          'Clasifica cada activo por tipo, controla su estado actual y registra numeros de serie para identificacion unica.',
          'Classify each asset by type, track its current status, and record serial numbers for unique identification.'
        ),

      },
      {
        name: s('Asignacion y desasignacion', 'Assignment and unassignment'),
        desc: s(
          'Asigna dispositivos a empleados con historial completo de quien tuvo cada equipo y cuando.',
          'Assign devices to employees with full history of who had each device and when.'
        ),

      },
      {
        name: s('Historial de eventos (event sourcing)', 'Event history (event sourcing)'),
        desc: s(
          'Registro inmutable de cada accion sobre cada activo — creacion, asignacion, incidencia, cambio de estado. Tu audit trail NIS2.',
          'Immutable log of every action on every asset — creation, assignment, incident, status change. Your NIS2 audit trail.'
        ),

      },
      {
        name: s('Codigos QR y codigos de barras', 'QR codes and barcodes'),
        desc: s(
          'Genera QR y Code 128 por activo. Escanea para acceder directamente al detalle. Imprimible para etiquetas fisicas.',
          'Generate QR and Code 128 per asset. Scan to access detail directly. Printable for physical labels.'
        ),

      },
      {
        name: s('Ubicaciones y movimiento', 'Locations and movement tracking'),
        desc: s(
          'Ubicaciones fisicas por empresa, movimiento automatico al asignar/enviar/dar de baja. Trail completo de localizacion.',
          'Physical locations per company, automatic movement on assign/ship/decommission. Full location trail.'
        ),

      },
      {
        name: s('Importacion masiva CSV', 'Bulk CSV import'),
        desc: s(
          'Importa cientos de activos de golpe desde un CSV. Ideal para migraciones desde Excel u otros sistemas.',
          'Import hundreds of assets at once from CSV. Ideal for migrations from Excel or other systems.'
        ),

      },
      {
        name: s('Ciclo de vida y garantias', 'Lifecycle and warranties'),
        desc: s(
          'Depreciacion, planificacion de fin de vida, ciclos de renovacion, lease vs compra, gestion de garantias y reclamaciones.',
          'Depreciation, end-of-life planning, renewal cycles, lease vs purchase, warranty management and claims.'
        ),

      },
      {
        name: s('Criticidad de activos y CMDB', 'Asset criticality and CMDB'),
        desc: s(
          'Clasifica activos por criticidad (Critico/Alto/Medio/Bajo). Mapea dependencias entre CIs. Analisis de impacto en negocio y grafo de dependencias.',
          'Classify assets by criticality (Critical/High/Medium/Low). Map CI dependencies. Business impact analysis and dependency graph.'
        ),

      },
      {
        name: s('Descubrimiento automatico de activos', 'Automatic asset discovery'),
        desc: s(
          'Escaneo de red para detectar dispositivos automaticamente. Con y sin agente. Sincroniza con tu inventario.',
          'Network scanning to detect devices automatically. Agent-based and agentless. Sync with your inventory.'
        ),

      },
    ],
  },
  {
    id: 'service-management',
    name: s('Gestion de servicios', 'Service Management'),
    icon: 'M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z',
    features: [
      {
        name: s('Solicitudes de servicio', 'Service requests'),
        desc: s(
          'Portal de empleado para crear solicitudes. Maquina de estados: enviada, en revision, en curso, resuelta/rechazada.',
          'Employee portal to create requests. State machine: submitted, in review, in progress, resolved/rejected.'
        ),

      },
      {
        name: s('Cola de tecnicos', 'Technician queue'),
        desc: s(
          'Los tecnicos reclaman y gestionan solicitudes. Comentarios, notas internas y cambios de prioridad.',
          'Technicians claim and manage requests. Comments, internal notes, and priority changes.'
        ),

      },
      {
        name: s('Tipificacion y aprobacion', 'Typification and approval'),
        desc: s(
          'Categorias estructuradas (reparacion, nuevo equipo, configuracion...). Sub-tipos, scoring de prioridad y flujo de aprobacion.',
          'Structured categories (repair, new equipment, configuration...). Sub-types, priority scoring, and approval workflow.'
        ),

      },
      {
        name: s('Clasificacion automatica con IA', 'AI-powered automatic classification'),
        desc: s(
          'La IA infiere categoria, sub-tipo y prioridad a partir de la descripcion del usuario. Mas preciso que la seleccion manual.',
          'AI infers category, sub-type, and priority from user description. More accurate than manual selection.'
        ),

      },
      {
        name: s('Base de conocimiento y autoservicio', 'Knowledge base and self-service'),
        desc: s(
          'Wiki con editor WYSIWYG (TipTap), versionado, busqueda full-text, articulos sugeridos por IA al crear tickets.',
          'Wiki with WYSIWYG editor (TipTap), versioning, full-text search, AI-suggested articles on ticket creation.'
        ),

      },
      {
        name: s('Gestion de SLA', 'SLA management'),
        desc: s(
          'Politicas SLA configurables por prioridad y categoria. Tiempos de respuesta/resolucion, escalado automatico, alertas de incumplimiento.',
          'Configurable SLA policies per priority and category. Response/resolution times, automatic escalation, breach alerts.'
        ),

      },
      {
        name: s('Citas y programacion', 'Appointment scheduling'),
        desc: s(
          'Agenda citas de soporte entre tecnicos y empleados. Calendario, disponibilidad, reservas, recordatorios y reprogramacion.',
          'Schedule support appointments between technicians and employees. Calendar, availability, booking, reminders, and rescheduling.'
        ),

      },
      {
        name: s('Gestion de cambios (ITIL)', 'Change management (ITIL)'),
        desc: s(
          'Flujo de cambios: solicitud, evaluacion de riesgo, aprobacion CAB, implementacion programada, rollback, revision post-implementacion.',
          'Change workflow: request, risk assessment, CAB approval, scheduled implementation, rollback, post-implementation review.'
        ),

      },
    ],
  },
  {
    id: 'operations',
    name: s('Operaciones TIC', 'IT Operations'),
    icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z',
    features: [
      {
        name: s('Perfiles de equipamiento por departamento', 'Department equipment profiles'),
        desc: s(
          'Define que equipo corresponde a cada rol: Tech -> Linux 32GB, Diseno -> MacBook Pro, Directores -> MacBook Air. Asignacion automatica.',
          'Define what equipment each role gets: Tech -> Linux 32GB, Design -> MacBook Pro, Heads -> MacBook Air. Automatic assignment.'
        ),

      },
      {
        name: s('Compras y presupuestos', 'Procurement and budgets'),
        desc: s(
          'Ordenes de compra, recepcion de mercancia, presupuesto por departamento, control de gasto con informes.',
          'Purchase orders, goods receipt, department budget allocation, spending control with reports.'
        ),

      },
      {
        name: s('Envios y logistica', 'Shipping and logistics'),
        desc: s(
          'Envia equipos a domicilio, oficinas o proveedor para reparacion. Seguimiento, direcciones, transportistas, devoluciones.',
          'Ship equipment to home, offices, or vendor for repair. Tracking, addresses, carriers, returns.'
        ),

      },
      {
        name: s('Mantenimiento programado', 'Scheduled maintenance'),
        desc: s(
          'Planes de mantenimiento preventivo y correctivo. Plantillas, calendario, asignacion de tecnicos, alertas de vencimiento.',
          'Preventive and corrective maintenance plans. Templates, calendar, technician assignment, overdue alerts.'
        ),

      },
      {
        name: s('Gestion de licencias de software', 'Software license management'),
        desc: s(
          'Licencias por usuario y departamento. Compliance de seats (usadas vs compradas), alertas de renovacion, coste por departamento.',
          'Licenses per user and department. Seat compliance (used vs purchased), renewal alerts, cost per department.'
        ),

      },
      {
        name: s('Onboarding / Offboarding automatizado', 'Automated onboarding / offboarding'),
        desc: s(
          'Workflows para altas (pack de equipo segun departamento y rol) y bajas (checklist de devolucion, desactivacion, recuperacion).',
          'Workflows for new hires (equipment pack by department and role) and departures (return checklist, deactivation, recovery).'
        ),

      },
      {
        name: s('Automatizacion de flujos de trabajo', 'Workflow automations'),
        desc: s(
          'Motor de reglas if-then: auto-asignar tickets, escalar tras SLA, notificar a manager, cerrar tickets resueltos, acciones por cambio de estado.',
          'If-then rule engine: auto-assign tickets, escalate after SLA, notify manager, close resolved tickets, trigger actions on status change.'
        ),

      },
      {
        name: s('Campos personalizados', 'Custom fields'),
        desc: s(
          'Campos definidos por el admin para activos, tickets y empresas — texto, numero, fecha, dropdown, multi-select con reglas de validacion.',
          'Admin-defined fields for assets, tickets, and companies — text, number, date, dropdown, multi-select with validation rules.'
        ),

      },
    ],
  },
  {
    id: 'security-compliance',
    name: s('Seguridad y compliance', 'Security & Compliance'),
    icon: 'M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z',
    features: [
      {
        name: s('Gestion de incidentes de seguridad', 'Security incident management'),
        desc: s(
          'Ciclo de vida completo: deteccion, triaje, contencion, erradicacion, recuperacion. Clasificacion P1-P4, vectores de ataque, sistemas afectados.',
          'Full lifecycle: detection, triage, containment, eradication, recovery. P1-P4 classification, attack vectors, affected systems.'
        ),

      },
      {
        name: s('Reporte regulatorio NIS2 (24h/72h/30d)', 'NIS2 regulatory reporting (24h/72h/30d)'),
        desc: s(
          'Cumplimiento automatico de los plazos NIS2: alerta temprana 24h, informe detallado 72h, informe final 30 dias. Temporizadores y alertas de escalado.',
          'Automatic NIS2 deadline compliance: 24h early warning, 72h detailed report, 30-day final report. Countdown timers and escalation alerts.'
        ),

      },
      {
        name: s('Registro de riesgos', 'Risk register'),
        desc: s(
          'Riesgos vinculados a activos, departamentos y proveedores. Matriz probabilidad x impacto, planes de mitigacion, dashboard con mapa de calor.',
          'Risks linked to assets, departments, and vendors. Likelihood x impact matrix, mitigation plans, dashboard with heat map.'
        ),

      },
      {
        name: s('Post-mortem e incidentes', 'Post-mortem and incidents'),
        desc: s(
          'Analisis de causa raiz, lecciones aprendidas, acciones correctivas vinculadas. Cross-reference con activos y proveedores afectados.',
          'Root cause analysis, lessons learned, linked corrective actions. Cross-reference with affected assets and vendors.'
        ),

      },
      {
        name: s('Audit trail completo', 'Complete audit trail'),
        desc: s(
          'Log inmutable de todas las acciones de usuario. Almacenamiento append-only. Exportacion GDPR. Evidencia vinculada a controles NIS2/DORA/ISO 27001.',
          'Immutable log of all user actions. Append-only storage. GDPR export. Evidence linked to NIS2/DORA/ISO 27001 controls.'
        ),

      },
      {
        name: s('Dashboard de compliance', 'Compliance dashboard'),
        desc: s(
          'Controles mapeados a NIS2, DORA e ISO 27001. Estado por control, recogida de evidencias, gap analysis, puntuacion de compliance, exportacion para auditores.',
          'Controls mapped to NIS2, DORA, and ISO 27001. Status per control, evidence collection, gap analysis, compliance score, auditor export.'
        ),

      },
      {
        name: s('Gestion de vulnerabilidades', 'Vulnerability management'),
        desc: s(
          'Seguimiento CVE por activo. CVSS scoring, creacion automatica de tickets de remediacion, tracking de parches, dashboard de exposicion.',
          'CVE tracking per asset. CVSS scoring, automatic remediation ticket creation, patch tracking, exposure dashboard.'
        ),

      },
      {
        name: s('Proveedores y riesgo de supply chain', 'Vendor and supply chain risk'),
        desc: s(
          'Directorio de proveedores con contratos, SLA, historial de incidentes. Cuestionarios de riesgo (DORA Art. 28), scoring de seguridad, mapeo de dependencias criticas.',
          'Vendor directory with contracts, SLAs, incident history. Risk questionnaires (DORA Art. 28), security scoring, critical dependency mapping.'
        ),

      },
    ],
  },
  {
    id: 'platform',
    name: s('Plataforma y conectividad', 'Platform & Connectivity'),
    icon: 'M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1',
    features: [
      {
        name: s('Dashboard en tiempo real', 'Real-time dashboard'),
        desc: s(
          'Metricas clave: activos por estado, solicitudes abiertas, SLA, costes, alertas de garantia y envejecimiento.',
          'Key metrics: assets by status, open requests, SLA, costs, warranty and aging alerts.'
        ),

      },
      {
        name: s('Notificaciones en tiempo real', 'Real-time notifications'),
        desc: s(
          'WebSockets para actualizaciones instantaneas. Notificaciones in-app, leidas/no leidas, eventos push.',
          'WebSockets for instant updates. In-app notifications, read/unread, push events.'
        ),

      },
      {
        name: s('Generacion de informes PDF', 'PDF report generation'),
        desc: s(
          'Informes asincronos con Celery. Plantillas HTML a PDF. Almacenamiento seguro. URL firmada para descarga.',
          'Async reports with Celery. HTML to PDF templates. Secure storage. Signed URL for download.'
        ),

      },
      {
        name: s('Roles y permisos granulares', 'Granular roles and permissions'),
        desc: s(
          'Empleados, tecnicos, administradores y super admin. Permisos por departamento y gestion de usuarios.',
          'Employees, technicians, admins, and super admin. Per-department permissions and user management.'
        ),

      },
      {
        name: s('Login con Google y Microsoft', 'Google and Microsoft login'),
        desc: s(
          'Botones de OAuth2 para Google y Microsoft. Verificacion de token, vinculacion por email, auto-creacion por dominio.',
          'OAuth2 buttons for Google and Microsoft. Token verification, email linking, auto-creation by domain.'
        ),

      },
      {
        name: s('API REST completa', 'Full REST API'),
        desc: s(
          'API documentada para integracion con tus herramientas existentes. Autenticacion JWT, multi-tenant.',
          'Documented API for integration with your existing tools. JWT authentication, multi-tenant.'
        ),

      },
      {
        name: s('Servidor MCP para agentes IA', 'MCP server for AI agents'),
        desc: s(
          'Expone DSM como servidor MCP. Los asistentes IA pueden gestionar activos, solicitudes, usuarios y dashboards via tool calls.',
          'Expose DSM as MCP server. AI assistants can manage assets, requests, users, and dashboards via tool calls.'
        ),

      },
      {
        name: s('Facturacion y suscripciones', 'Billing and subscriptions'),
        desc: s(
          'Gestion de suscripciones con Stripe. Planes Free/Premium/Enterprise. Portal de facturas, limites de uso, trial gratuito.',
          'Subscription management with Stripe. Free/Premium/Enterprise plans. Invoice portal, usage limits, free trial.'
        ),

      },
      {
        name: s('Bilingue (ES/EN)', 'Bilingual (ES/EN)'),
        desc: s(
          'Interfaz completa en espanol e ingles. Selector de idioma en la app.',
          'Full interface in Spanish and English. In-app language selector.'
        ),

      },
      {
        name: s('SSO empresarial y sincronizacion de directorio', 'Enterprise SSO and directory sync'),
        desc: s(
          'SAML/OIDC, LDAP/Active Directory sync, provisionamiento/desprovisionamiento automatico, mapeo grupo-a-rol.',
          'SAML/OIDC, LDAP/Active Directory sync, automatic provisioning/deprovisioning, group-to-role mapping.'
        ),

      },
      {
        name: s('Intake multi-canal', 'Multi-channel intake'),
        desc: s(
          'Email-to-ticket, integracion Slack/Teams, chatbot para crear tickets sin entrar en la app.',
          'Email-to-ticket, Slack/Teams integration, chatbot for guided ticket creation without entering the app.'
        ),

      },
      {
        name: s('App movil / PWA', 'Mobile app / PWA'),
        desc: s(
          'PWA para tecnicos y empleados. Escaneo QR con camara, actualizacion de tickets en campo, push notifications, soporte offline.',
          'PWA for technicians and employees. QR scanning with camera, field ticket updates, push notifications, offline support.'
        ),

      },
      {
        name: s('Encuestas y feedback', 'Surveys and feedback'),
        desc: s(
          'CSAT post-resolucion, encuestas de decision para planificacion de compras, feedback de onboarding, metricas de satisfaccion.',
          'Post-resolution CSAT, decision polls for purchase planning, onboarding feedback, satisfaction metrics.'
        ),

      },
    ],
  },
];
