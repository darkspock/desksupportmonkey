import { Calendar, Clock, CheckCircle2, XCircle } from "lucide-react"
import { Card } from "@/components/ui/card"
import type { Appointment } from "@/lib/appointments-data"

export function AppointmentStats({ appointments }: { appointments: Appointment[] }) {
  const stats = {
    total: appointments.length,
    programadas: appointments.filter((a) => a.status === "programada").length,
    completadas: appointments.filter((a) => a.status === "completada").length,
    canceladas: appointments.filter((a) => a.status === "cancelada").length,
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card className="p-4 bg-card border-border">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">Total Citas</p>
            <p className="text-2xl font-semibold text-foreground mt-1">{stats.total}</p>
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <Calendar className="h-5 w-5 text-primary" />
          </div>
        </div>
      </Card>

      <Card className="p-4 bg-card border-border">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">Programadas</p>
            <p className="text-2xl font-semibold text-foreground mt-1">{stats.programadas}</p>
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <Clock className="h-5 w-5 text-primary" />
          </div>
        </div>
      </Card>

      <Card className="p-4 bg-card border-border">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">Completadas</p>
            <p className="text-2xl font-semibold text-foreground mt-1">{stats.completadas}</p>
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-success/15">
            <CheckCircle2 className="h-5 w-5 text-success" />
          </div>
        </div>
      </Card>

      <Card className="p-4 bg-card border-border">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">Canceladas</p>
            <p className="text-2xl font-semibold text-foreground mt-1">{stats.canceladas}</p>
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
            <XCircle className="h-5 w-5 text-muted-foreground" />
          </div>
        </div>
      </Card>
    </div>
  )
}
