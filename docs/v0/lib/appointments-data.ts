export type AppointmentType = "soporte_presencial" | "soporte_remoto" | "instalacion" | "formacion"

export type AppointmentStatus = "programada" | "en_curso" | "completada" | "cancelada"

export type Appointment = {
  id: string
  title: string
  type: AppointmentType
  status: AppointmentStatus
  date: string
  startTime: string
  endTime: string
  technician: string
  user: string
  userEmail: string
  department: string
  location?: string
  notes?: string
  linkedTicketId?: string
  linkedTicketCode?: string
}

export const APPOINTMENT_TYPE_CONFIG: Record<AppointmentType, { label: string; className: string; color: string }> = {
  soporte_presencial: {
    label: "Soporte presencial",
    className: "bg-primary/10 text-primary border-primary/30",
    color: "#4555d8",
  },
  soporte_remoto: {
    label: "Soporte remoto",
    className: "bg-success/15 text-success border-success/30",
    color: "#16a34a",
  },
  instalacion: {
    label: "Instalacion de equipo",
    className: "bg-warning/15 text-warning-foreground border-warning/30",
    color: "#ca8a04",
  },
  formacion: {
    label: "Formacion",
    className: "bg-chart-3/15 text-chart-3 border-chart-3/30",
    color: "#8b5cf6",
  },
}

export const APPOINTMENT_STATUS_CONFIG: Record<AppointmentStatus, { label: string; className: string }> = {
  programada: {
    label: "Programada",
    className: "bg-primary/10 text-primary border-primary/30",
  },
  en_curso: {
    label: "En curso",
    className: "bg-warning/15 text-warning-foreground border-warning/30",
  },
  completada: {
    label: "Completada",
    className: "bg-success/15 text-success border-success/30",
  },
  cancelada: {
    label: "Cancelada",
    className: "bg-muted/50 text-muted-foreground border-border",
  },
}

export const MOCK_APPOINTMENTS: Appointment[] = [
  {
    id: "1",
    title: "Revisar pantalla en negro",
    type: "soporte_presencial",
    status: "programada",
    date: "2026-02-19",
    startTime: "12:00",
    endTime: "12:30",
    technician: "Pedro Sanchez",
    user: "Carlos Martinez",
    userEmail: "carlos.martinez@company.com",
    department: "Ingenieria",
    location: "Oficina - Planta 3, Puesto 32",
    notes: "Revisar monitor Dell UltraSharp tras actualizacion macOS",
    linkedTicketId: "1",
    linkedTicketCode: "TKT-001",
  },
  {
    id: "2",
    title: "Setup MacBook nueva diseñadora",
    type: "instalacion",
    status: "programada",
    date: "2026-02-24",
    startTime: "09:00",
    endTime: "10:30",
    technician: "Pedro Sanchez",
    user: "Laura Fernandez",
    userEmail: "laura.fernandez@company.com",
    department: "Diseño",
    location: "Oficina - Planta 2, Puesto 15",
    notes: "Configurar MacBook, iPad, Figma y Adobe Suite para onboarding",
    linkedTicketId: "2",
    linkedTicketCode: "TKT-002",
  },
  {
    id: "3",
    title: "Diagnostico WiFi",
    type: "soporte_remoto",
    status: "programada",
    date: "2026-02-19",
    startTime: "14:00",
    endTime: "14:30",
    technician: "Pedro Sanchez",
    user: "Miguel Ruiz",
    userEmail: "miguel.ruiz@company.com",
    department: "Ventas",
    notes: "Revisar desconexiones WiFi constantes via Zoom",
    linkedTicketId: "5",
    linkedTicketCode: "TKT-005",
  },
  {
    id: "4",
    title: "Formacion Google Workspace",
    type: "formacion",
    status: "programada",
    date: "2026-02-20",
    startTime: "10:00",
    endTime: "11:30",
    technician: "Ana Garcia",
    user: "Equipo Marketing",
    userEmail: "marketing@company.com",
    department: "Marketing",
    location: "Sala de reuniones B",
    notes: "Sesion de formacion en Google Drive, Docs, Sheets para el equipo de marketing",
  },
  {
    id: "5",
    title: "Instalacion setup marketing analysts",
    type: "instalacion",
    status: "programada",
    date: "2026-03-03",
    startTime: "09:00",
    endTime: "12:00",
    technician: "Pedro Sanchez",
    user: "3 nuevos analysts",
    userEmail: "roberto.diaz@company.com",
    department: "Marketing",
    location: "Oficina - Planta 1",
    notes: "Setup completo de 3 portatiles y configuracion de accesos",
    linkedTicketId: "6",
    linkedTicketCode: "TKT-006",
  },
  {
    id: "6",
    title: "Soporte Excel avanzado",
    type: "soporte_remoto",
    status: "completada",
    date: "2026-02-18",
    startTime: "15:00",
    endTime: "15:45",
    technician: "Ana Garcia",
    user: "Patricia Ruiz",
    userEmail: "patricia.ruiz@company.com",
    department: "Finanzas",
    notes: "Ayuda con formulas y macros en Excel",
  },
  {
    id: "7",
    title: "Revision impresora planta 2",
    type: "soporte_presencial",
    status: "completada",
    date: "2026-02-18",
    startTime: "11:00",
    endTime: "11:30",
    technician: "Pedro Sanchez",
    user: "Equipo Diseño",
    userEmail: "diseno@company.com",
    department: "Diseño",
    location: "Oficina - Planta 2, Area comun",
    notes: "Impresora HP con atascos de papel",
  },
  {
    id: "8",
    title: "Setup VPN para trabajo remoto",
    type: "soporte_remoto",
    status: "programada",
    date: "2026-02-19",
    startTime: "16:00",
    endTime: "16:30",
    technician: "Ana Garcia",
    user: "Javier Morales",
    userEmail: "javier.morales@company.com",
    department: "Desarrollo",
    notes: "Configurar VPN corporativa para acceso remoto seguro",
  },
  {
    id: "9",
    title: "Formacion Slack y herramientas colaboracion",
    type: "formacion",
    status: "programada",
    date: "2026-02-21",
    startTime: "11:00",
    endTime: "12:00",
    technician: "Ana Garcia",
    user: "Nuevos empleados",
    userEmail: "rrhh@company.com",
    department: "Recursos Humanos",
    location: "Sala de reuniones A",
    notes: "Onboarding session para nuevos empleados sobre herramientas de colaboracion",
  },
  {
    id: "10",
    title: "Instalacion dual monitor",
    type: "instalacion",
    status: "programada",
    date: "2026-02-20",
    startTime: "14:00",
    endTime: "14:45",
    technician: "Pedro Sanchez",
    user: "Elena Torres",
    userEmail: "elena.torres@company.com",
    department: "Diseño",
    location: "Oficina - Planta 2, Puesto 22",
    notes: "Instalar segundo monitor y configurar setup dual",
  },
]

// Helper function to get appointments for a specific date
export function getAppointmentsByDate(date: string): Appointment[] {
  return MOCK_APPOINTMENTS.filter((apt) => apt.date === date)
}

// Helper function to get appointments for a date range
export function getAppointmentsInRange(startDate: string, endDate: string): Appointment[] {
  return MOCK_APPOINTMENTS.filter((apt) => apt.date >= startDate && apt.date <= endDate)
}

// Helper to format time
export function formatTime(time: string): string {
  return time
}

// Helper to get month days
export function getMonthDays(year: number, month: number): Date[] {
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const days: Date[] = []

  // Add previous month days to fill the first week
  const firstDayOfWeek = firstDay.getDay()
  const daysFromPrevMonth = firstDayOfWeek === 0 ? 6 : firstDayOfWeek - 1
  for (let i = daysFromPrevMonth; i > 0; i--) {
    days.push(new Date(year, month, 1 - i))
  }

  // Add current month days
  for (let i = 1; i <= lastDay.getDate(); i++) {
    days.push(new Date(year, month, i))
  }

  // Add next month days to fill the last week
  const lastDayOfWeek = lastDay.getDay()
  const daysToNextMonth = lastDayOfWeek === 0 ? 0 : 7 - lastDayOfWeek
  for (let i = 1; i <= daysToNextMonth; i++) {
    days.push(new Date(year, month + 1, i))
  }

  return days
}

export function formatDateToISO(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, "0")
  const day = String(date.getDate()).padStart(2, "0")
  return `${year}-${month}-${day}`
}
