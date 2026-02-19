"use client"

import Link from "next/link"
import { AlertCircle, Eye, Laptop, MessageSquare, MoreVertical, Printer, UserPlus } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import type { Ticket, TicketType } from "@/lib/tickets-data"
import { TICKET_STATUS_CONFIG, TICKET_PRIORITY_CONFIG, TICKET_TYPE_CONFIG } from "@/lib/tickets-data"

function formatDate(dateStr: string) {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 60) return `hace ${diffMins}min`
  if (diffHours < 24) return `hace ${diffHours}h`
  if (diffDays < 7) return `hace ${diffDays}d`
  
  return new Intl.DateTimeFormat("es-ES", {
    day: "2-digit",
    month: "short",
  }).format(date)
}

const TYPE_ICON_MAP: Record<TicketType, React.ElementType> = {
  equipo_no_funciona: AlertCircle,
  nuevo_ordenador: Laptop,
  onboarding: UserPlus,
}

const NEXT_ACTION: Record<
  string,
  { label: string; icon: React.ElementType; variant: "default" | "outline" | "secondary" | "ghost" } | null
> = {
  abierto: {
    label: "Responder",
    icon: MessageSquare,
    variant: "default",
  },
  en_progreso: {
    label: "Ver detalles",
    icon: Eye,
    variant: "outline",
  },
  esperando_respuesta: {
    label: "Responder",
    icon: MessageSquare,
    variant: "default",
  },
  resuelto: {
    label: "Ver detalles",
    icon: Eye,
    variant: "ghost",
  },
  cerrado: null,
}

export function TicketTable({ tickets }: { tickets: Ticket[] }) {
  if (tickets.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-card py-16">
        <p className="text-sm text-muted-foreground">No se encontraron tickets</p>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-border bg-card overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead className="pl-4 w-12">Tipo</TableHead>
            <TableHead>Titulo</TableHead>
            <TableHead className="hidden md:table-cell">Solicitante</TableHead>
            <TableHead className="hidden sm:table-cell">Actualizado</TableHead>
            <TableHead>Estado</TableHead>
            <TableHead className="hidden lg:table-cell">Prioridad</TableHead>
            <TableHead className="w-24 pr-4">
              <span className="sr-only">Acciones</span>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {tickets.map((ticket) => {
            const statusConfig = TICKET_STATUS_CONFIG[ticket.status]
            const priorityConfig = TICKET_PRIORITY_CONFIG[ticket.priority]
            const typeConfig = TICKET_TYPE_CONFIG[ticket.type]
            const TypeIcon = TYPE_ICON_MAP[ticket.type]
            const nextAction = NEXT_ACTION[ticket.status]

            return (
              <TableRow key={ticket.id} className="group">
                <TableCell className="pl-4">
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary/10">
                        <TypeIcon className="h-4 w-4 text-primary" />
                      </div>
                    </TooltipTrigger>
                    <TooltipContent side="right">
                      {typeConfig.label}
                    </TooltipContent>
                  </Tooltip>
                </TableCell>
                <TableCell>
                  <Link href={`/tickets/${ticket.id}`} className="group/link">
                    <div className="flex flex-col gap-0.5">
                      <span className="text-sm font-medium text-foreground group-hover/link:text-primary transition-colors line-clamp-1">
                        {ticket.title}
                      </span>
                      <span className="text-xs text-muted-foreground font-mono">{ticket.code}</span>
                    </div>
                  </Link>
                </TableCell>
                <TableCell className="hidden md:table-cell">
                  <div className="flex flex-col">
                    <span className="text-sm text-foreground">{ticket.reporter}</span>
                    <span className="text-xs text-muted-foreground">{ticket.department}</span>
                  </div>
                </TableCell>
                <TableCell className="hidden sm:table-cell">
                  <span className="text-sm text-muted-foreground">{formatDate(ticket.updatedAt)}</span>
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className={statusConfig.className}>
                    {statusConfig.label}
                  </Badge>
                </TableCell>
                <TableCell className="hidden lg:table-cell">
                  <Badge variant="outline" className={priorityConfig.className}>
                    {priorityConfig.label}
                  </Badge>
                </TableCell>
                <TableCell className="pr-4">
                  <div className="flex items-center justify-end gap-1">
                    <Tooltip>
                      <TooltipTrigger asChild>
                        {nextAction ? (
                          <Button variant={nextAction.variant} size="icon" className="h-8 w-8" asChild>
                            <Link href={`/tickets/${ticket.id}`}>
                              <nextAction.icon className="h-4 w-4" />
                              <span className="sr-only">{nextAction.label}</span>
                            </Link>
                          </Button>
                        ) : (
                          <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground" asChild>
                            <Link href={`/tickets/${ticket.id}`}>
                              <Eye className="h-4 w-4" />
                              <span className="sr-only">Ver</span>
                            </Link>
                          </Button>
                        )}
                      </TooltipTrigger>
                      <TooltipContent side="left">
                        {nextAction ? nextAction.label : "Ver ticket"}
                      </TooltipContent>
                    </Tooltip>

                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity data-[state=open]:opacity-100">
                          <MoreVertical className="h-4 w-4" />
                          <span className="sr-only">Mas acciones</span>
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="w-48">
                        <DropdownMenuItem asChild>
                          <Link href={`/tickets/${ticket.id}`} className="gap-2">
                            <Eye className="h-4 w-4" />
                            Ver detalle
                          </Link>
                        </DropdownMenuItem>
                        <DropdownMenuItem className="gap-2">
                          <Printer className="h-4 w-4" />
                          Imprimir
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem className="gap-2">
                          Marcar como resuelto
                        </DropdownMenuItem>
                        <DropdownMenuItem className="gap-2">
                          Cerrar ticket
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
}
