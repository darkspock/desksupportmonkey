export type TicketType = "equipo_no_funciona" | "nuevo_ordenador" | "onboarding"

export type TicketStatus = "abierto" | "en_progreso" | "esperando_respuesta" | "resuelto" | "cerrado"

export type TicketPriority = "critica" | "alta" | "media" | "baja"

export type TicketMessage = {
  id: string
  author: string
  role: string
  content: string
  timestamp: string
  isInternal: boolean
}

export type Ticket = {
  id: string
  code: string
  title: string
  type: TicketType
  status: TicketStatus
  priority: TicketPriority
  reporter: string
  reporterEmail: string
  department: string
  assignee?: string
  createdAt: string
  updatedAt: string
  description: string
  messages: TicketMessage[]
}

export const TICKET_TYPE_CONFIG: Record<TicketType, { label: string; description: string; icon: string }> = {
  equipo_no_funciona: {
    label: "Mi ordenador no funciona",
    description: "Problemas tecnicos con equipamiento existente",
    icon: "AlertCircle",
  },
  nuevo_ordenador: {
    label: "Nuevo ordenador",
    description: "Solicitud de equipamiento nuevo",
    icon: "Laptop",
  },
  onboarding: {
    label: "Onboarding de empleado",
    description: "Configuracion para nuevos empleados",
    icon: "UserPlus",
  },
}

export const TICKET_STATUS_CONFIG: Record<TicketStatus, { label: string; className: string }> = {
  abierto: {
    label: "Abierto",
    className: "bg-primary/10 text-primary border-primary/30",
  },
  en_progreso: {
    label: "En progreso",
    className: "bg-warning/15 text-warning-foreground border-warning/30",
  },
  esperando_respuesta: {
    label: "Esperando respuesta",
    className: "bg-muted text-muted-foreground border-border",
  },
  resuelto: {
    label: "Resuelto",
    className: "bg-success/15 text-success border-success/30",
  },
  cerrado: {
    label: "Cerrado",
    className: "bg-muted/50 text-muted-foreground border-border",
  },
}

export const TICKET_PRIORITY_CONFIG: Record<TicketPriority, { label: string; className: string }> = {
  critica: { label: "Critica", className: "bg-destructive text-destructive-foreground border-destructive" },
  alta: { label: "Alta", className: "bg-destructive/10 text-destructive border-destructive/30" },
  media: { label: "Media", className: "bg-warning/15 text-warning-foreground border-warning/30" },
  baja: { label: "Baja", className: "bg-muted text-muted-foreground border-border" },
}

export const MOCK_TICKETS: Ticket[] = [
  {
    id: "1",
    code: "TKT-001",
    title: "Pantalla en negro tras actualizacion",
    type: "equipo_no_funciona",
    status: "en_progreso",
    priority: "alta",
    reporter: "Carlos Martinez",
    reporterEmail: "carlos.martinez@company.com",
    department: "Ingenieria",
    assignee: "Pedro Sanchez",
    createdAt: "2026-02-19T09:30:00Z",
    updatedAt: "2026-02-19T11:45:00Z",
    description: "Despues de la actualizacion de macOS, la pantalla externa se queda en negro. Ya he reiniciado el ordenador varias veces pero el problema persiste.",
    messages: [
      {
        id: "m1",
        author: "Carlos Martinez",
        role: "Usuario",
        content: "Despues de la actualizacion de macOS, la pantalla externa se queda en negro. Ya he reiniciado el ordenador varias veces pero el problema persiste.",
        timestamp: "2026-02-19T09:30:00Z",
        isInternal: false,
      },
      {
        id: "m2",
        author: "Pedro Sanchez",
        role: "IT Support",
        content: "Hola Carlos, voy a revisar tu caso. Has probado a desconectar y reconectar el cable? Que modelo de monitor tienes?",
        timestamp: "2026-02-19T10:15:00Z",
        isInternal: false,
      },
      {
        id: "m3",
        author: "Carlos Martinez",
        role: "Usuario",
        content: "Si, lo he probado. Es un Dell UltraSharp 27. Antes de la actualizacion funcionaba perfectamente.",
        timestamp: "2026-02-19T10:45:00Z",
        isInternal: false,
      },
      {
        id: "m4",
        author: "Pedro Sanchez",
        role: "IT Support",
        content: "Perfecto. Voy a ir a tu puesto en 30 minutos para revisarlo en persona.",
        timestamp: "2026-02-19T11:45:00Z",
        isInternal: false,
      },
    ],
  },
  {
    id: "2",
    code: "TKT-002",
    title: "Setup completo para nueva diseñadora",
    type: "onboarding",
    status: "abierto",
    priority: "media",
    reporter: "Carmen Ortiz",
    reporterEmail: "carmen.ortiz@company.com",
    department: "Recursos Humanos",
    assignee: "Pedro Sanchez",
    createdAt: "2026-02-18T14:20:00Z",
    updatedAt: "2026-02-18T14:20:00Z",
    description: "Laura Fernandez se incorpora el lunes 24 de febrero. Necesita MacBook, iPad para testing, acceso a Figma y Adobe Suite, y configuracion de email corporativo.",
    messages: [
      {
        id: "m1",
        author: "Carmen Ortiz",
        role: "HR",
        content: "Laura Fernandez se incorpora el lunes 24 de febrero. Necesita MacBook, iPad para testing, acceso a Figma y Adobe Suite, y configuracion de email corporativo.",
        timestamp: "2026-02-18T14:20:00Z",
        isInternal: false,
      },
    ],
  },
  {
    id: "3",
    code: "TKT-003",
    title: "Teclado con teclas que no responden",
    type: "equipo_no_funciona",
    status: "resuelto",
    priority: "media",
    reporter: "Isabel Moreno",
    reporterEmail: "isabel.moreno@company.com",
    department: "Marketing",
    assignee: "Pedro Sanchez",
    createdAt: "2026-02-17T10:00:00Z",
    updatedAt: "2026-02-18T16:30:00Z",
    description: "Varias teclas de mi teclado Keychron no responden correctamente. Especialmente la barra espaciadora y las teclas de direccion.",
    messages: [
      {
        id: "m1",
        author: "Isabel Moreno",
        role: "Usuario",
        content: "Varias teclas de mi teclado Keychron no responden correctamente. Especialmente la barra espaciadora y las teclas de direccion.",
        timestamp: "2026-02-17T10:00:00Z",
        isInternal: false,
      },
      {
        id: "m2",
        author: "Pedro Sanchez",
        role: "IT Support",
        content: "Hola Isabel, voy a tramitar un teclado de reemplazo. Te llegara mañana.",
        timestamp: "2026-02-17T11:30:00Z",
        isInternal: false,
      },
      {
        id: "m3",
        author: "Isabel Moreno",
        role: "Usuario",
        content: "Perfecto, gracias! Ya he recibido el teclado nuevo y funciona genial.",
        timestamp: "2026-02-18T16:30:00Z",
        isInternal: false,
      },
    ],
  },
  {
    id: "4",
    code: "TKT-004",
    title: "MacBook Pro para developer senior",
    type: "nuevo_ordenador",
    status: "abierto",
    priority: "alta",
    reporter: "Ana Lopez",
    reporterEmail: "ana.lopez@company.com",
    department: "Ingenieria",
    assignee: "Pedro Sanchez",
    createdAt: "2026-02-19T08:00:00Z",
    updatedAt: "2026-02-19T08:00:00Z",
    description: "Andres Gutierrez necesita un MacBook Pro 16\" con M3 Max para trabajar en el proyecto de Machine Learning. Inicio previsto: 1 de marzo.",
    messages: [
      {
        id: "m1",
        author: "Ana Lopez",
        role: "Manager",
        content: "Andres Gutierrez necesita un MacBook Pro 16\" con M3 Max para trabajar en el proyecto de Machine Learning. Inicio previsto: 1 de marzo.",
        timestamp: "2026-02-19T08:00:00Z",
        isInternal: false,
      },
    ],
  },
  {
    id: "5",
    code: "TKT-005",
    title: "WiFi desconexiones constantes",
    type: "equipo_no_funciona",
    status: "esperando_respuesta",
    priority: "media",
    reporter: "Miguel Ruiz",
    reporterEmail: "miguel.ruiz@company.com",
    department: "Ventas",
    assignee: "Pedro Sanchez",
    createdAt: "2026-02-18T16:45:00Z",
    updatedAt: "2026-02-19T09:20:00Z",
    description: "Mi portatil se desconecta del WiFi cada 10-15 minutos. Tengo que reconectarme manualmente. Esto esta afectando mis llamadas con clientes.",
    messages: [
      {
        id: "m1",
        author: "Miguel Ruiz",
        role: "Usuario",
        content: "Mi portatil se desconecta del WiFi cada 10-15 minutos. Tengo que reconectarme manualmente. Esto esta afectando mis llamadas con clientes.",
        timestamp: "2026-02-18T16:45:00Z",
        isInternal: false,
      },
      {
        id: "m2",
        author: "Pedro Sanchez",
        role: "IT Support",
        content: "Hola Miguel, vamos a revisar tu equipo. Puedes probar a olvidar la red WiFi y volver a conectarte? Ve a Configuracion > WiFi > [nombre red] > Olvidar esta red. Despues vuelve a conectarte introduciendo la contraseña.",
        timestamp: "2026-02-19T09:20:00Z",
        isInternal: false,
      },
    ],
  },
  {
    id: "6",
    code: "TKT-006",
    title: "Setup onboarding 3 nuevos de Marketing",
    type: "onboarding",
    status: "en_progreso",
    priority: "alta",
    reporter: "Roberto Diaz",
    reporterEmail: "roberto.diaz@company.com",
    department: "Marketing",
    assignee: "Pedro Sanchez",
    createdAt: "2026-02-16T11:00:00Z",
    updatedAt: "2026-02-18T15:30:00Z",
    description: "Tres nuevos marketing analysts se incorporan el 3 de marzo. Necesitan portatiles, acceso a herramientas de analytics (Google Analytics, Mixpanel), y cuentas en redes sociales corporativas.",
    messages: [
      {
        id: "m1",
        author: "Roberto Diaz",
        role: "Manager",
        content: "Tres nuevos marketing analysts se incorporan el 3 de marzo. Necesitan portatiles, acceso a herramientas de analytics (Google Analytics, Mixpanel), y cuentas en redes sociales corporativas.",
        timestamp: "2026-02-16T11:00:00Z",
        isInternal: false,
      },
      {
        id: "m2",
        author: "Pedro Sanchez",
        role: "IT Support",
        content: "Perfecto Roberto. Ya tengo 2 portatiles preparados. El tercero llegara el viernes. Voy a coordinar con el equipo para preparar los accesos.",
        timestamp: "2026-02-18T15:30:00Z",
        isInternal: false,
      },
    ],
  },
]
