export type OrderStatus = "pendiente" | "en_revision" | "aprobado" | "rechazado" | "entregado"

export type ApprovalStep = {
  id: string
  label: string
  approver: string
  role: string
  status: "completado" | "pendiente" | "rechazado" | "actual"
  date?: string
  comment?: string
}

export type OrderItem = {
  id: string
  name: string
  category: string
  quantity: number
  unitPrice: number
}

export type Order = {
  id: string
  code: string
  employee: string
  employeeRole: string
  department: string
  date: string
  status: OrderStatus
  items: OrderItem[]
  total: number
  priority: "alta" | "media" | "baja"
  approvalSteps: ApprovalStep[]
  notes?: string
}

export const STATUS_CONFIG: Record<OrderStatus, { label: string; className: string }> = {
  pendiente: {
    label: "Pendiente",
    className: "bg-warning/15 text-warning-foreground border-warning/30",
  },
  en_revision: {
    label: "En Revision",
    className: "bg-primary/10 text-primary border-primary/30",
  },
  aprobado: {
    label: "Aprobado",
    className: "bg-success/15 text-success border-success/30",
  },
  rechazado: {
    label: "Rechazado",
    className: "bg-destructive/10 text-destructive border-destructive/30",
  },
  entregado: {
    label: "Entregado",
    className: "bg-muted text-muted-foreground border-border",
  },
}

export const PRIORITY_CONFIG: Record<string, { label: string; className: string }> = {
  alta: { label: "Alta", className: "bg-destructive/10 text-destructive border-destructive/30" },
  media: { label: "Media", className: "bg-warning/15 text-warning-foreground border-warning/30" },
  baja: { label: "Baja", className: "bg-muted text-muted-foreground border-border" },
}

export const EQUIPMENT_CATALOG = [
  { id: "eq-1", name: 'MacBook Pro 16"', category: "Portatil", unitPrice: 2499 },
  { id: "eq-2", name: "Dell UltraSharp 27\" 4K", category: "Monitor", unitPrice: 620 },
  { id: "eq-3", name: "Logitech MX Master 3S", category: "Periferico", unitPrice: 99 },
  { id: "eq-4", name: "Keychron Q1 Pro", category: "Periferico", unitPrice: 199 },
  { id: "eq-5", name: "Herman Miller Aeron", category: "Mobiliario", unitPrice: 1395 },
  { id: "eq-6", name: "iPhone 15 Pro", category: "Movil", unitPrice: 1199 },
  { id: "eq-7", name: "AirPods Pro 2", category: "Audio", unitPrice: 249 },
  { id: "eq-8", name: "iPad Air M2", category: "Tablet", unitPrice: 799 },
  { id: "eq-9", name: "Thunderbolt Dock", category: "Accesorio", unitPrice: 349 },
  { id: "eq-10", name: "Webcam Logitech Brio", category: "Periferico", unitPrice: 199 },
]

export const DEPARTMENTS = [
  "Ingenieria",
  "Diseno",
  "Marketing",
  "Ventas",
  "Recursos Humanos",
  "Finanzas",
  "Operaciones",
]

export const MOCK_ORDERS: Order[] = [
  {
    id: "1",
    code: "PO-2026-001",
    employee: "Carlos Martinez",
    employeeRole: "Senior Developer",
    department: "Ingenieria",
    date: "2026-02-15",
    status: "aprobado",
    priority: "alta",
    items: [
      { id: "i1", name: 'MacBook Pro 16"', category: "Portatil", quantity: 1, unitPrice: 2499 },
      { id: "i2", name: "Dell UltraSharp 27\" 4K", category: "Monitor", quantity: 2, unitPrice: 620 },
    ],
    total: 3739,
    approvalSteps: [
      { id: "s1", label: "Solicitud Enviada", approver: "Carlos Martinez", role: "Solicitante", status: "completado", date: "2026-02-15", comment: "Necesito actualizar mi equipo para el proyecto de ML." },
      { id: "s2", label: "Revision de Manager", approver: "Ana Lopez", role: "Engineering Manager", status: "completado", date: "2026-02-16", comment: "Aprobado. Es necesario para el proyecto." },
      { id: "s3", label: "Aprobacion de IT", approver: "Pedro Sanchez", role: "IT Director", status: "completado", date: "2026-02-17", comment: "Equipamiento compatible con la infraestructura." },
      { id: "s4", label: "Aprobacion Financiera", approver: "Maria Garcia", role: "CFO", status: "completado", date: "2026-02-18", comment: "Dentro del presupuesto trimestral." },
      { id: "s5", label: "Procesamiento", approver: "Sistema", role: "Automatico", status: "completado", date: "2026-02-19" },
    ],
    notes: "Urgente: necesario para el proyecto de Machine Learning que inicia en marzo.",
  },
  {
    id: "2",
    code: "PO-2026-002",
    employee: "Laura Fernandez",
    employeeRole: "UX Designer",
    department: "Diseno",
    date: "2026-02-16",
    status: "en_revision",
    priority: "media",
    items: [
      { id: "i3", name: "iPad Air M2", category: "Tablet", quantity: 1, unitPrice: 799 },
      { id: "i4", name: "AirPods Pro 2", category: "Audio", quantity: 1, unitPrice: 249 },
    ],
    total: 1048,
    approvalSteps: [
      { id: "s1", label: "Solicitud Enviada", approver: "Laura Fernandez", role: "Solicitante", status: "completado", date: "2026-02-16", comment: "Para pruebas de usabilidad y prototipos." },
      { id: "s2", label: "Revision de Manager", approver: "Diego Torres", role: "Design Lead", status: "actual", date: undefined },
      { id: "s3", label: "Aprobacion de IT", approver: "Pedro Sanchez", role: "IT Director", status: "pendiente" },
      { id: "s4", label: "Aprobacion Financiera", approver: "Maria Garcia", role: "CFO", status: "pendiente" },
      { id: "s5", label: "Procesamiento", approver: "Sistema", role: "Automatico", status: "pendiente" },
    ],
  },
  {
    id: "3",
    code: "PO-2026-003",
    employee: "Miguel Ruiz",
    employeeRole: "Sales Executive",
    department: "Ventas",
    date: "2026-02-14",
    status: "rechazado",
    priority: "baja",
    items: [
      { id: "i5", name: "Herman Miller Aeron", category: "Mobiliario", quantity: 1, unitPrice: 1395 },
    ],
    total: 1395,
    approvalSteps: [
      { id: "s1", label: "Solicitud Enviada", approver: "Miguel Ruiz", role: "Solicitante", status: "completado", date: "2026-02-14", comment: "Silla ergonomica por recomendacion medica." },
      { id: "s2", label: "Revision de Manager", approver: "Sofia Navarro", role: "Sales Manager", status: "completado", date: "2026-02-15", comment: "Aprobado por motivo de salud." },
      { id: "s3", label: "Aprobacion Financiera", approver: "Maria Garcia", role: "CFO", status: "rechazado", date: "2026-02-16", comment: "Presupuesto del departamento agotado. Reprogramar para Q2." },
      { id: "s4", label: "Procesamiento", approver: "Sistema", role: "Automatico", status: "pendiente" },
    ],
    notes: "Necesidad por recomendacion medica.",
  },
  {
    id: "4",
    code: "PO-2026-004",
    employee: "Isabel Moreno",
    employeeRole: "Marketing Analyst",
    department: "Marketing",
    date: "2026-02-17",
    status: "pendiente",
    priority: "media",
    items: [
      { id: "i6", name: "Logitech MX Master 3S", category: "Periferico", quantity: 1, unitPrice: 99 },
      { id: "i7", name: "Keychron Q1 Pro", category: "Periferico", quantity: 1, unitPrice: 199 },
      { id: "i8", name: "Webcam Logitech Brio", category: "Periferico", quantity: 1, unitPrice: 199 },
    ],
    total: 497,
    approvalSteps: [
      { id: "s1", label: "Solicitud Enviada", approver: "Isabel Moreno", role: "Solicitante", status: "completado", date: "2026-02-17", comment: "Perifericos para oficina en casa." },
      { id: "s2", label: "Revision de Manager", approver: "Roberto Diaz", role: "Marketing Director", status: "pendiente" },
      { id: "s3", label: "Aprobacion de IT", approver: "Pedro Sanchez", role: "IT Director", status: "pendiente" },
      { id: "s4", label: "Procesamiento", approver: "Sistema", role: "Automatico", status: "pendiente" },
    ],
  },
  {
    id: "5",
    code: "PO-2026-005",
    employee: "Andres Gutierrez",
    employeeRole: "DevOps Engineer",
    department: "Ingenieria",
    date: "2026-02-10",
    status: "entregado",
    priority: "alta",
    items: [
      { id: "i9", name: 'MacBook Pro 16"', category: "Portatil", quantity: 1, unitPrice: 2499 },
      { id: "i10", name: "Thunderbolt Dock", category: "Accesorio", quantity: 1, unitPrice: 349 },
      { id: "i11", name: "Dell UltraSharp 27\" 4K", category: "Monitor", quantity: 1, unitPrice: 620 },
    ],
    total: 3468,
    approvalSteps: [
      { id: "s1", label: "Solicitud Enviada", approver: "Andres Gutierrez", role: "Solicitante", status: "completado", date: "2026-02-10" },
      { id: "s2", label: "Revision de Manager", approver: "Ana Lopez", role: "Engineering Manager", status: "completado", date: "2026-02-11", comment: "Aprobado." },
      { id: "s3", label: "Aprobacion de IT", approver: "Pedro Sanchez", role: "IT Director", status: "completado", date: "2026-02-12" },
      { id: "s4", label: "Aprobacion Financiera", approver: "Maria Garcia", role: "CFO", status: "completado", date: "2026-02-13" },
      { id: "s5", label: "Procesamiento", approver: "Sistema", role: "Automatico", status: "completado", date: "2026-02-14" },
    ],
  },
  {
    id: "6",
    code: "PO-2026-006",
    employee: "Elena Vega",
    employeeRole: "HR Specialist",
    department: "Recursos Humanos",
    date: "2026-02-18",
    status: "pendiente",
    priority: "baja",
    items: [
      { id: "i12", name: "Logitech MX Master 3S", category: "Periferico", quantity: 3, unitPrice: 99 },
    ],
    total: 297,
    approvalSteps: [
      { id: "s1", label: "Solicitud Enviada", approver: "Elena Vega", role: "Solicitante", status: "completado", date: "2026-02-18", comment: "Ratones para nuevas incorporaciones." },
      { id: "s2", label: "Revision de Manager", approver: "Carmen Ortiz", role: "HR Director", status: "pendiente" },
      { id: "s3", label: "Procesamiento", approver: "Sistema", role: "Automatico", status: "pendiente" },
    ],
    notes: "Para onboarding de 3 nuevos empleados en marzo.",
  },
]
