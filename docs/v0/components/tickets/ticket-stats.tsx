"use client"

import { AlertCircle, CheckCircle2, Clock, Ticket } from "lucide-react"
import type { Ticket } from "@/lib/tickets-data"

export function TicketStats({ tickets }: { tickets: Ticket[] }) {
  const stats = {
    total: tickets.length,
    abierto: tickets.filter((t) => t.status === "abierto").length,
    en_progreso: tickets.filter((t) => t.status === "en_progreso").length,
    resuelto: tickets.filter((t) => t.status === "resuelto").length,
  }

  const statCards = [
    {
      label: "Total Tickets",
      value: stats.total,
      icon: Ticket,
      className: "text-foreground",
    },
    {
      label: "Abiertos",
      value: stats.abierto,
      icon: AlertCircle,
      className: "text-primary",
    },
    {
      label: "En progreso",
      value: stats.en_progreso,
      icon: Clock,
      className: "text-warning-foreground",
    },
    {
      label: "Resueltos",
      value: stats.resuelto,
      icon: CheckCircle2,
      className: "text-success",
    },
  ]

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {statCards.map((stat) => (
        <div
          key={stat.label}
          className="flex flex-col gap-2 rounded-lg border border-border bg-card p-4"
        >
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">{stat.label}</span>
            <stat.icon className={`h-4 w-4 ${stat.className}`} />
          </div>
          <div className={`text-2xl font-bold ${stat.className}`}>{stat.value}</div>
        </div>
      ))}
    </div>
  )
}
