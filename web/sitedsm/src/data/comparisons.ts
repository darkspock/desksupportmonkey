export interface ComparisonFeature {
  name: { es: string; en: string };
  dsm: boolean | string;
  competitor: boolean | string;
}

export interface ComparisonData {
  slug: string;
  competitor: string;
  logo_color: string;
  headline: { es: string; en: string };
  subtitle: { es: string; en: string };
  intro: { es: string; en: string };
  dsm_summary: { es: string; en: string };
  competitor_summary: { es: string; en: string };
  features: ComparisonFeature[];
  pricing_dsm: { es: string; en: string };
  pricing_competitor: { es: string; en: string };
  verdict: { es: string; en: string };
  best_for_dsm: { es: string; en: string };
  best_for_competitor: { es: string; en: string };
}

export const comparisons: ComparisonData[] = [
  {
    slug: 'excel',
    competitor: 'Excel / Hojas de calculo',
    logo_color: 'text-green-600 bg-green-50',
    headline: {
      es: 'DSM Control vs Excel',
      en: 'DSM Control vs Excel',
    },
    subtitle: {
      es: 'Por que una hoja de calculo no es suficiente para cumplir NIS2',
      en: 'Why a spreadsheet is not enough for NIS2 compliance',
    },
    intro: {
      es: 'El 67% de las PYMEs europeas gestionan sus activos IT en hojas de calculo. Funciona hasta que un auditor pide trazabilidad, un portatil desaparece, o NIS2 exige documentar cada incidencia vinculada a un dispositivo. Excel no fue disenado para esto.',
      en: '67% of European SMBs manage their IT assets in spreadsheets. It works until an auditor asks for traceability, a laptop disappears, or NIS2 requires documenting every incident linked to a device. Excel was not designed for this.',
    },
    dsm_summary: {
      es: 'Plataforma completa de gestion del ciclo de vida de activos TIC con trazabilidad NIS2, incidencias vinculadas a dispositivos y audit trail exportable.',
      en: 'Complete IT asset lifecycle management platform with NIS2 traceability, device-linked incidents, and exportable audit trail.',
    },
    competitor_summary: {
      es: 'Hoja de calculo generica. Flexible pero sin estructura, sin audit trail, sin vinculacion entre incidencias y activos, sin control de versiones real.',
      en: 'Generic spreadsheet. Flexible but with no structure, no audit trail, no link between incidents and assets, no real version control.',
    },
    features: [
      { name: { es: 'Inventario de activos centralizado', en: 'Centralized asset inventory' }, dsm: true, competitor: '⚠️' },
      { name: { es: 'Audit trail automatico', en: 'Automatic audit trail' }, dsm: true, competitor: false },
      { name: { es: 'Incidencias vinculadas a dispositivos', en: 'Incidents linked to devices' }, dsm: true, competitor: false },
      { name: { es: 'Historial de cambios por activo', en: 'Change history per asset' }, dsm: true, competitor: false },
      { name: { es: 'Multiples usuarios simultaneos', en: 'Multiple simultaneous users' }, dsm: true, competitor: '⚠️' },
      { name: { es: 'Roles y permisos', en: 'Roles and permissions' }, dsm: true, competitor: false },
      { name: { es: 'Ciclo de vida completo', en: 'Full lifecycle management' }, dsm: true, competitor: false },
      { name: { es: 'Dashboard con metricas', en: 'Dashboard with metrics' }, dsm: true, competitor: false },
      { name: { es: 'Exportacion para auditores NIS2', en: 'NIS2 auditor export' }, dsm: true, competitor: false },
      { name: { es: 'Coste inicial cero', en: 'Zero initial cost' }, dsm: true, competitor: true },
    ],
    pricing_dsm: {
      es: 'Desde €49/mes. Plan gratuito para empresas de hasta 10 empleados. Self-hosted gratis.',
      en: 'From €49/month. Free plan for companies up to 10 employees. Self-hosted free.',
    },
    pricing_competitor: {
      es: 'Gratis (Microsoft 365) o incluido en Google Workspace. Pero el coste real es el tiempo de mantenimiento y el riesgo de compliance.',
      en: 'Free (Microsoft 365) or included in Google Workspace. But the real cost is maintenance time and compliance risk.',
    },
    verdict: {
      es: 'Excel funciona para 5 portatiles. No funciona cuando un auditor NIS2 pide trazabilidad completa de cada dispositivo y cada incidencia. DSM Control convierte tu inventario caótico en un sistema de compliance en menos de un dia.',
      en: 'Excel works for 5 laptops. It does not work when a NIS2 auditor asks for full traceability of every device and every incident. DSM Control turns your chaotic inventory into a compliance system in less than a day.',
    },
    best_for_dsm: {
      es: 'Empresas de +10 empleados que necesitan compliance NIS2 o simplemente quieren dejar de gestionar activos en hojas de calculo.',
      en: 'Companies with 10+ employees that need NIS2 compliance or simply want to stop managing assets in spreadsheets.',
    },
    best_for_competitor: {
      es: 'Equipos de menos de 5 personas sin requisitos de compliance ni necesidad de trazabilidad.',
      en: 'Teams of fewer than 5 people with no compliance requirements or traceability needs.',
    },
  },
  {
    slug: 'freshservice',
    competitor: 'Freshservice',
    logo_color: 'text-emerald-600 bg-emerald-50',
    headline: {
      es: 'DSM Control vs Freshservice',
      en: 'DSM Control vs Freshservice',
    },
    subtitle: {
      es: 'Gestion de activos TIC sin la trampa del pricing por agente',
      en: 'IT asset management without the per-agent pricing trap',
    },
    intro: {
      es: 'Freshservice es una herramienta ITSM excelente, pero su pricing penaliza a las PYMEs: cobran por agente ($19-119/mes) Y por activos ($75-1,500/mes adicionales). Una empresa de 50 empleados con 3 tecnicos puede acabar pagando €400-600+/mes. DSM Control cobra por tamano de empresa: €99/mes para hasta 100 empleados, todo incluido.',
      en: 'Freshservice is an excellent ITSM tool, but its pricing penalizes SMBs: they charge per agent ($19-119/month) AND per asset ($75-1,500/month extra). A 50-employee company with 3 technicians can end up paying €400-600+/month. DSM Control charges by company size: €99/month for up to 100 employees, everything included.',
    },
    dsm_summary: {
      es: 'Plataforma de gestion de activos TIC con ciclo de vida completo, incidencias vinculadas y NIS2. Precio fijo por tamano de empresa.',
      en: 'IT asset management platform with full lifecycle, linked incidents, and NIS2. Flat pricing by company size.',
    },
    competitor_summary: {
      es: 'ITSM completo (tickets, problemas, cambios, releases) con modulo de activos. Potente pero caro para PYMEs. Sin posicionamiento NIS2.',
      en: 'Full ITSM (tickets, problems, changes, releases) with asset module. Powerful but expensive for SMBs. No NIS2 positioning.',
    },
    features: [
      { name: { es: 'Inventario de activos', en: 'Asset inventory' }, dsm: true, competitor: true },
      { name: { es: 'Incidencias vinculadas a activos', en: 'Incidents linked to assets' }, dsm: true, competitor: true },
      { name: { es: 'Ciclo de vida completo (compra a baja)', en: 'Full lifecycle (purchase to decommission)' }, dsm: true, competitor: '⚠️' },
      { name: { es: 'NIS2 audit trail', en: 'NIS2 audit trail' }, dsm: true, competitor: false },
      { name: { es: 'Precio fijo sin coste por agente', en: 'Flat price with no per-agent fee' }, dsm: true, competitor: false },
      { name: { es: 'Sin coste adicional por activos', en: 'No extra cost per asset' }, dsm: true, competitor: false },
      { name: { es: 'Gestion de cambios (ITIL)', en: 'Change management (ITIL)' }, dsm: false, competitor: true },
      { name: { es: 'Autodiscovery de red', en: 'Network autodiscovery' }, dsm: false, competitor: true },
      { name: { es: 'Datos alojados en la UE', en: 'EU-hosted data' }, dsm: true, competitor: false },
    ],
    pricing_dsm: {
      es: 'Starter €49/mes (hasta 25 emp.) · Growth €99/mes (hasta 100 emp.) · Scale €199/mes (100+ emp.). Todo incluido.',
      en: 'Starter €49/mo (up to 25 emp.) · Growth €99/mo (up to 100 emp.) · Scale €199/mo (100+ emp.). Everything included.',
    },
    pricing_competitor: {
      es: 'Starter $19/agente/mes + Asset Management desde $75/mes (500 activos). Enterprise: $119/agente/mes + $1,500/mes activos ilimitados. Una empresa de 50 personas con 3 tecnicos: ~$432-1,857/mes.',
      en: 'Starter $19/agent/mo + Asset Management from $75/mo (500 assets). Enterprise: $119/agent/mo + $1,500/mo unlimited assets. A 50-person company with 3 technicians: ~$432-1,857/mo.',
    },
    verdict: {
      es: 'Freshservice es ideal si necesitas ITIL completo (cambios, problemas, releases) y tienes presupuesto enterprise. Si lo que necesitas es gestionar activos, vincular incidencias y cumplir NIS2 sin gastar +€400/mes, DSM Control hace exactamente eso a una fraccion del coste.',
      en: 'Freshservice is ideal if you need full ITIL (changes, problems, releases) and have an enterprise budget. If what you need is to manage assets, link incidents, and comply with NIS2 without spending +€400/month, DSM Control does exactly that at a fraction of the cost.',
    },
    best_for_dsm: {
      es: 'PYMEs de 10-300 empleados que necesitan gestion de activos + incidencias + compliance NIS2 con un pricing predecible.',
      en: 'SMBs with 10-300 employees that need asset management + incidents + NIS2 compliance with predictable pricing.',
    },
    best_for_competitor: {
      es: 'Empresas de +300 empleados con equipos IT grandes que necesitan ITIL completo, autodiscovery y workflows complejos.',
      en: 'Companies with 300+ employees with large IT teams that need full ITIL, autodiscovery, and complex workflows.',
    },
  },
  {
    slug: 'snipe-it',
    competitor: 'Snipe-IT',
    logo_color: 'text-purple-600 bg-purple-50',
    headline: {
      es: 'DSM Control vs Snipe-IT',
      en: 'DSM Control vs Snipe-IT',
    },
    subtitle: {
      es: 'El inventario que Snipe-IT tiene + las incidencias que Snipe-IT no tiene',
      en: 'The inventory Snipe-IT has + the incidents Snipe-IT doesn\'t',
    },
    intro: {
      es: 'Snipe-IT es el proyecto open source de gestion de activos mas popular (~12,000 estrellas en GitHub) y tiene un ciclo de vida solido. Pero tiene una carencia critica: no tiene gestion de incidencias. No puedes vincular un ticket a un activo. Es la limitacion mas citada en sus reviews. DSM Control une ambos mundos.',
      en: 'Snipe-IT is the most popular open source asset management project (~12,000 GitHub stars) with a solid lifecycle. But it has one critical gap: no incident management. You cannot link a ticket to an asset. It is the most cited limitation in reviews. DSM Control bridges both worlds.',
    },
    dsm_summary: {
      es: 'Inventario de activos + incidencias vinculadas + ciclo de vida + NIS2 audit trail. Todo en una plataforma.',
      en: 'Asset inventory + linked incidents + lifecycle + NIS2 audit trail. All in one platform.',
    },
    competitor_summary: {
      es: 'Inventario de activos open source excelente. Check-in/out, licencias, garantias. Pero cero gestion de incidencias o tickets.',
      en: 'Excellent open source asset inventory. Check-in/out, licenses, warranties. But zero incident management or ticketing.',
    },
    features: [
      { name: { es: 'Inventario de activos', en: 'Asset inventory' }, dsm: true, competitor: true },
      { name: { es: 'Check-in / check-out', en: 'Check-in / check-out' }, dsm: true, competitor: true },
      { name: { es: 'Gestion de incidencias', en: 'Incident management' }, dsm: true, competitor: false },
      { name: { es: 'Incidencias vinculadas a activos', en: 'Incidents linked to assets' }, dsm: true, competitor: false },
      { name: { es: 'NIS2 audit trail', en: 'NIS2 audit trail' }, dsm: true, competitor: false },
      { name: { es: 'Ordenes de compra', en: 'Purchase orders' }, dsm: true, competitor: true },
      { name: { es: 'Mantenimiento preventivo', en: 'Preventive maintenance' }, dsm: true, competitor: false },
      { name: { es: 'SaaS cloud gestionado', en: 'Managed cloud SaaS' }, dsm: true, competitor: true },
      { name: { es: 'Gestion de licencias software', en: 'Software license management' }, dsm: false, competitor: true },
    ],
    pricing_dsm: {
      es: 'Starter €49/mes · Growth €99/mes · Scale €199/mes. Self-hosted gratis (AGPL).',
      en: 'Starter €49/mo · Growth €99/mo · Scale €199/mo. Self-hosted free (AGPL).',
    },
    pricing_competitor: {
      es: 'Self-hosted gratis (AGPL). Cloud: $39.99-249/mes dependiendo de activos.',
      en: 'Self-hosted free (AGPL). Cloud: $39.99-249/month depending on assets.',
    },
    verdict: {
      es: 'Si solo necesitas un inventario de activos, Snipe-IT es una opcion solida y madura. Pero si necesitas vincular incidencias a dispositivos — que es exactamente lo que exige NIS2 — Snipe-IT no puede hacerlo. DSM Control es Snipe-IT + un modulo completo de incidencias + NIS2 compliance.',
      en: 'If you only need an asset inventory, Snipe-IT is a solid and mature option. But if you need to link incidents to devices — which is exactly what NIS2 requires — Snipe-IT cannot do it. DSM Control is Snipe-IT + a complete incident module + NIS2 compliance.',
    },
    best_for_dsm: {
      es: 'Empresas que necesitan inventario + incidencias + compliance en una sola herramienta, sin integrar multiples productos.',
      en: 'Companies that need inventory + incidents + compliance in a single tool, without integrating multiple products.',
    },
    best_for_competitor: {
      es: 'Equipos que solo necesitan inventario puro de hardware/software y gestion de licencias, sin modulo de incidencias.',
      en: 'Teams that only need pure hardware/software inventory and license management, without an incident module.',
    },
  },
  {
    slug: 'lansweeper',
    competitor: 'Lansweeper',
    logo_color: 'text-sky-600 bg-sky-50',
    headline: {
      es: 'DSM Control vs Lansweeper',
      en: 'DSM Control vs Lansweeper',
    },
    subtitle: {
      es: 'Lansweeper descubre tus dispositivos. DSM Control gestiona su ciclo de vida.',
      en: 'Lansweeper discovers your devices. DSM Control manages their lifecycle.',
    },
    intro: {
      es: 'Lansweeper es el competidor mas fuerte en narrativa NIS2: tiene paginas dedicadas, checklists y contenido de compliance. Pero es fundamentalmente una herramienta de descubrimiento de red. No tiene service desk, no vincula incidencias a activos, y no gestiona el ciclo de vida (compra, asignacion, baja). Para eso necesitas integrarlo con Freshservice o Jira.',
      en: 'Lansweeper is the strongest competitor on NIS2 narrative: they have dedicated pages, checklists, and compliance content. But it is fundamentally a network discovery tool. It has no service desk, does not link incidents to assets, and does not manage the lifecycle (purchase, assignment, decommission). For that you need to integrate it with Freshservice or Jira.',
    },
    dsm_summary: {
      es: 'Plataforma todo-en-uno: inventario + incidencias + ciclo de vida + compliance NIS2. Sin necesidad de integrar con terceros.',
      en: 'All-in-one platform: inventory + incidents + lifecycle + NIS2 compliance. No need to integrate with third parties.',
    },
    competitor_summary: {
      es: 'Herramienta de descubrimiento y auditoria de red. Escanea dispositivos automaticamente. Fuerte en NIS2 marketing. Sin service desk ni ciclo de vida.',
      en: 'Network discovery and audit tool. Automatically scans devices. Strong NIS2 marketing. No service desk or lifecycle management.',
    },
    features: [
      { name: { es: 'Inventario de activos', en: 'Asset inventory' }, dsm: true, competitor: true },
      { name: { es: 'Autodiscovery de red', en: 'Network autodiscovery' }, dsm: false, competitor: true },
      { name: { es: 'Gestion de incidencias', en: 'Incident management' }, dsm: true, competitor: false },
      { name: { es: 'Incidencias vinculadas a activos', en: 'Incidents linked to assets' }, dsm: true, competitor: false },
      { name: { es: 'Ciclo de vida completo', en: 'Full lifecycle management' }, dsm: true, competitor: false },
      { name: { es: 'Ordenes de compra y proveedores', en: 'Purchase orders and vendors' }, dsm: true, competitor: false },
      { name: { es: 'Mantenimiento preventivo', en: 'Preventive maintenance' }, dsm: true, competitor: false },
      { name: { es: 'NIS2 compliance posicionamiento', en: 'NIS2 compliance positioning' }, dsm: true, competitor: true },
      { name: { es: 'Pricing < €200/mes para PYMEs', en: 'Pricing < €200/mo for SMBs' }, dsm: true, competitor: false },
    ],
    pricing_dsm: {
      es: 'Starter €49/mes · Growth €99/mes · Scale €199/mes. Self-hosted gratis.',
      en: 'Starter €49/mo · Growth €99/mo · Scale €199/mo. Self-hosted free.',
    },
    pricing_competitor: {
      es: 'Free hasta 100 activos. Starter €199/mes. Pro y Enterprise: contactar ventas (estimacion: €500+/mes para PYMEs).',
      en: 'Free up to 100 assets. Starter €199/month. Pro and Enterprise: contact sales (estimate: €500+/month for SMBs).',
    },
    verdict: {
      es: 'Lansweeper es excelente si tu prioridad es descubrir que hay en tu red automaticamente. Pero NIS2 no solo pide saber que tienes — pide documentar quien lo usa, que incidencias ha tenido, y todo su historial. DSM Control cubre lo que Lansweeper no puede: el ciclo de vida completo con incidencias vinculadas.',
      en: 'Lansweeper is excellent if your priority is to automatically discover what is on your network. But NIS2 does not just ask you to know what you have — it asks you to document who uses it, what incidents it has had, and its full history. DSM Control covers what Lansweeper cannot: the complete lifecycle with linked incidents.',
    },
    best_for_dsm: {
      es: 'PYMEs que necesitan gestionar el ciclo de vida completo de sus activos con incidencias y compliance, sin pagar €500+/mes ni integrar multiples herramientas.',
      en: 'SMBs that need to manage the full lifecycle of their assets with incidents and compliance, without paying €500+/month or integrating multiple tools.',
    },
    best_for_competitor: {
      es: 'Empresas medianas/grandes con equipos de seguridad que priorizan descubrimiento automatico de red y ya tienen un ITSM separado.',
      en: 'Medium/large companies with security teams that prioritize automatic network discovery and already have a separate ITSM.',
    },
  },
  {
    slug: 'glpi',
    competitor: 'GLPI',
    logo_color: 'text-orange-600 bg-orange-50',
    headline: {
      es: 'DSM Control vs GLPI',
      en: 'DSM Control vs GLPI',
    },
    subtitle: {
      es: 'La misma funcionalidad, pero en una plataforma moderna y sin necesidad de DevOps',
      en: 'The same functionality, but on a modern platform with no DevOps required',
    },
    intro: {
      es: 'GLPI es el equivalente funcional mas cercano a DSM Control: tiene ITAM completo, service desk con tickets vinculados a activos, y es open source. Pero su stack PHP es de principios de los 2000, requiere conocimientos de DevOps para instalarlo, y su interfaz no ha evolucionado. No tiene ninguna narrativa NIS2.',
      en: 'GLPI is the closest functional equivalent to DSM Control: it has full ITAM, a service desk with tickets linked to assets, and it is open source. But its PHP stack is from the early 2000s, requires DevOps knowledge to install, and its interface has not evolved. It has zero NIS2 narrative.',
    },
    dsm_summary: {
      es: 'Stack moderno (FastAPI + React), SaaS-first, NIS2 compliance integrado, pricing simple, UX actual.',
      en: 'Modern stack (FastAPI + React), SaaS-first, integrated NIS2 compliance, simple pricing, current UX.',
    },
    competitor_summary: {
      es: 'Funcionalidad completa pero stack PHP legacy, UX datada, requiere instalacion y mantenimiento DevOps. Sin NIS2. Cloud es un afterthought.',
      en: 'Complete functionality but legacy PHP stack, dated UX, requires installation and DevOps maintenance. No NIS2. Cloud is an afterthought.',
    },
    features: [
      { name: { es: 'Inventario de activos', en: 'Asset inventory' }, dsm: true, competitor: true },
      { name: { es: 'Incidencias vinculadas a activos', en: 'Incidents linked to assets' }, dsm: true, competitor: true },
      { name: { es: 'Ciclo de vida completo', en: 'Full lifecycle management' }, dsm: true, competitor: true },
      { name: { es: 'NIS2 audit trail', en: 'NIS2 audit trail' }, dsm: true, competitor: false },
      { name: { es: 'SaaS cloud sin instalacion', en: 'SaaS cloud, no installation' }, dsm: true, competitor: '⚠️' },
      { name: { es: 'UX moderna (React + Tailwind)', en: 'Modern UX (React + Tailwind)' }, dsm: true, competitor: false },
      { name: { es: 'API REST moderna', en: 'Modern REST API' }, dsm: true, competitor: '⚠️' },
      { name: { es: 'Plugins y extensiones', en: 'Plugins and extensions' }, dsm: false, competitor: true },
      { name: { es: 'Comunidad establecida (20+ anos)', en: 'Established community (20+ years)' }, dsm: false, competitor: true },
    ],
    pricing_dsm: {
      es: 'Starter €49/mes · Growth €99/mes · Scale €199/mes. Self-hosted gratis (AGPL).',
      en: 'Starter €49/mo · Growth €99/mo · Scale €199/mo. Self-hosted free (AGPL).',
    },
    pricing_competitor: {
      es: 'Self-hosted gratis (GPLv3). Cloud: GLPI Network desde €19/mes (basico) hasta €45+/mes con soporte.',
      en: 'Self-hosted free (GPLv3). Cloud: GLPI Network from €19/month (basic) to €45+/month with support.',
    },
    verdict: {
      es: 'GLPI tiene una funcionalidad comparable. Si ya lo tienes instalado y funcionando, no hay razon urgente para migrar. Pero si estas evaluando herramientas desde cero, DSM Control ofrece la misma cobertura funcional con una experiencia moderna, SaaS-first, NIS2 ready, y sin necesidad de mantener un servidor PHP.',
      en: 'GLPI has comparable functionality. If you already have it installed and running, there is no urgent reason to migrate. But if you are evaluating tools from scratch, DSM Control offers the same functional coverage with a modern experience, SaaS-first, NIS2 ready, and no need to maintain a PHP server.',
    },
    best_for_dsm: {
      es: 'Empresas que evaluan herramientas por primera vez y quieren SaaS moderno con compliance NIS2 sin gestion de infraestructura.',
      en: 'Companies evaluating tools for the first time that want modern SaaS with NIS2 compliance without infrastructure management.',
    },
    best_for_competitor: {
      es: 'Organizaciones que ya usan GLPI, tienen equipo DevOps, y necesitan el ecosistema de plugins de GLPI.',
      en: 'Organizations that already use GLPI, have a DevOps team, and need GLPI\'s plugin ecosystem.',
    },
  },
];
