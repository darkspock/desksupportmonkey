"use client"

import Link from "next/link"
import { Calendar, Clock, User, Mail, Building2, MapPin, Ticket, Check, X } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { APPOINTMENT_TYPE_CONFIG, APPOINTMENT_STATUS_CONFIG, type Appointment } from "@/lib/appointments-data"

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return new Intl.DateTimeFormat("es-ES", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(date)
}

export function AppointmentDetail({ appointment }: { appointment: Appointment }) {
  const typeConfig = APPOINTMENT_TYPE_CONFIG[appointment.type]
  const statusConfig = APPOINTMENT_STATUS_CONFIG[appointment.status]

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      {/* Main Content */}
      <div className="lg:col-span-2 flex flex-col gap-6">
        <Card className="p-6 border-border">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="text-2xl font-semibold text-foreground mb-2">{appointment.title}</h2>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className={typeConfig.className}>
                  {typeConfig.label}
                </Badge>
                <Badge variant="outline" className={statusConfig.className}>
                  {statusConfig.label}
                </Badge>
              </div>
            </div>
          </div>

          <Separator className="my-4" />

          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <Calendar className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div>
                <p className="text-sm font-medium text-foreground">Fecha</p>
                <p className="text-sm text-muted-foreground capitalize">{formatDate(appointment.date)}</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <Clock className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div>
                <p className="text-sm font-medium text-foreground">Horario</p>
                <p className="text-sm text-muted-foreground">
                  {appointment.startTime} - {appointment.endTime}
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <User className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div>
                <p className="text-sm font-medium text-foreground">Usuario</p>
                <p className="text-sm text-muted-foreground">{appointment.user}</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <Mail className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div>
                <p className="text-sm font-medium text-foreground">Email</p>
                <p className="text-sm text-muted-foreground">{appointment.userEmail}</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <Building2 className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div>
                <p className="text-sm font-medium text-foreground">Departamento</p>
                <p className="text-sm text-muted-foreground">{appointment.department}</p>
              </div>
            </div>

            {appointment.location && (
              <div className="flex items-start gap-3">
                <MapPin className="h-5 w-5 text-muted-foreground mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-foreground">Ubicacion</p>
                  <p className="text-sm text-muted-foreground">{appointment.location}</p>
                </div>
              </div>
            )}

            {appointment.linkedTicketCode && (
              <div className="flex items-start gap-3">
                <Ticket className="h-5 w-5 text-muted-foreground mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-foreground">Ticket relacionado</p>
                  <Link
                    href={`/tickets/${appointment.linkedTicketId}`}
                    className="text-sm text-primary hover:underline"
                  >
                    {appointment.linkedTicketCode}
                  </Link>
                </div>
              </div>
            )}
          </div>

          {appointment.notes && (
            <>
              <Separator className="my-4" />
              <div>
                <p className="text-sm font-medium text-foreground mb-2">Notas</p>
                <p className="text-sm text-muted-foreground leading-relaxed">{appointment.notes}</p>
              </div>
            </>
          )}
        </Card>
      </div>

      {/* Sidebar */}
      <div className="flex flex-col gap-4">
        <Card className="p-4 border-border">
          <h3 className="text-sm font-semibold text-foreground mb-3">Tecnico asignado</h3>
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
              <span className="text-sm font-medium text-primary">
                {appointment.technician
                  .split(" ")
                  .map((n) => n[0])
                  .join("")}
              </span>
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">{appointment.technician}</p>
              <p className="text-xs text-muted-foreground">IT Support</p>
            </div>
          </div>
        </Card>

        {appointment.status === "programada" && (
          <Card className="p-4 border-border">
            <h3 className="text-sm font-semibold text-foreground mb-3">Acciones</h3>
            <div className="flex flex-col gap-2">
              <Button size="sm" className="w-full gap-2">
                <Check className="h-4 w-4" />
                Completar cita
              </Button>
              <Button size="sm" variant="outline" className="w-full gap-2">
                <X className="h-4 w-4" />
                Cancelar cita
              </Button>
            </div>
          </Card>
        )}
      </div>
    </div>
  )
}
