"use client"

import { AlertCircle, Calendar, CheckCircle2, Clock, Laptop, User, UserPlus } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import type { Ticket } from "@/lib/tickets-data"
import { TICKET_STATUS_CONFIG, TICKET_PRIORITY_CONFIG, TICKET_TYPE_CONFIG } from "@/lib/tickets-data"
import { TicketConversation } from "./ticket-conversation"

const TYPE_ICON_MAP = {
  equipo_no_funciona: AlertCircle,
  nuevo_ordenador: Laptop,
  onboarding: UserPlus,
}

function formatDate(dateStr: string) {
  return new Intl.DateTimeFormat("es-ES", {
    day: "2-digit",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(dateStr))
}

export function TicketDetail({ ticket }: { ticket: Ticket }) {
  const statusConfig = TICKET_STATUS_CONFIG[ticket.status]
  const priorityConfig = TICKET_PRIORITY_CONFIG[ticket.priority]
  const typeConfig = TICKET_TYPE_CONFIG[ticket.type]
  const TypeIcon = TYPE_ICON_MAP[ticket.type]

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Main content */}
      <div className="lg:col-span-2 space-y-6">
        <div className="rounded-lg border border-border bg-card p-6 space-y-4">
          <div className="flex items-start gap-3">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-primary/10">
              <TypeIcon className="h-6 w-6 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2">
                <Badge variant="outline" className={typeConfig ? "text-xs" : ""}>
                  {typeConfig.label}
                </Badge>
                <span className="text-xs text-muted-foreground font-mono">{ticket.code}</span>
              </div>
              <h1 className="text-2xl font-bold text-foreground mb-2">{ticket.title}</h1>
              <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
                {ticket.description}
              </p>
            </div>
          </div>
        </div>

        <TicketConversation messages={ticket.messages} />
      </div>

      {/* Sidebar */}
      <div className="space-y-4">
        <div className="rounded-lg border border-border bg-card p-4 space-y-4">
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Estado</h3>
            <Badge variant="outline" className={statusConfig.className}>
              {statusConfig.label}
            </Badge>
          </div>

          <Separator />

          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Prioridad</h3>
            <Badge variant="outline" className={priorityConfig.className}>
              {priorityConfig.label}
            </Badge>
          </div>

          <Separator />

          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Solicitante</h3>
            <div className="flex items-start gap-2">
              <User className="h-4 w-4 text-muted-foreground mt-0.5" />
              <div className="flex flex-col">
                <span className="text-sm font-medium text-foreground">{ticket.reporter}</span>
                <span className="text-xs text-muted-foreground">{ticket.reporterEmail}</span>
                <span className="text-xs text-muted-foreground">{ticket.department}</span>
              </div>
            </div>
          </div>

          {ticket.assignee && (
            <>
              <Separator />
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-2">Asignado a</h3>
                <div className="flex items-center gap-2">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10">
                    <span className="text-xs font-medium text-primary">
                      {ticket.assignee.split(" ").map((n) => n[0]).join("")}
                    </span>
                  </div>
                  <span className="text-sm text-foreground">{ticket.assignee}</span>
                </div>
              </div>
            </>
          )}

          <Separator />

          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Fechas</h3>
            <div className="space-y-2">
              <div className="flex items-start gap-2 text-xs">
                <Calendar className="h-3.5 w-3.5 text-muted-foreground mt-0.5" />
                <div className="flex flex-col">
                  <span className="text-muted-foreground">Creado</span>
                  <span className="text-foreground">{formatDate(ticket.createdAt)}</span>
                </div>
              </div>
              <div className="flex items-start gap-2 text-xs">
                <Clock className="h-3.5 w-3.5 text-muted-foreground mt-0.5" />
                <div className="flex flex-col">
                  <span className="text-muted-foreground">Actualizado</span>
                  <span className="text-foreground">{formatDate(ticket.updatedAt)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {ticket.status !== "cerrado" && ticket.status !== "resuelto" && (
          <div className="rounded-lg border border-border bg-card p-4 space-y-2">
            <h3 className="text-sm font-medium text-foreground mb-3">Acciones</h3>
            <Button className="w-full" variant="default" size="sm">
              <CheckCircle2 className="mr-2 h-4 w-4" />
              Marcar como resuelto
            </Button>
            <Button className="w-full" variant="outline" size="sm">
              Cambiar prioridad
            </Button>
            <Button className="w-full" variant="outline" size="sm">
              Reasignar
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
