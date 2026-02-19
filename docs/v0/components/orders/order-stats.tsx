"use client"

import { ClipboardList, Clock, CheckCircle2, XCircle, Truck } from "lucide-react"
import type { Order } from "@/lib/orders-data"

type StatItem = {
  label: string
  value: number
  icon: React.ElementType
  colorClass: string
  bgClass: string
}

export function OrderStats({ orders }: { orders: Order[] }) {
  const stats: StatItem[] = [
    {
      label: "Total",
      value: orders.length,
      icon: ClipboardList,
      colorClass: "text-primary",
      bgClass: "bg-primary/10",
    },
    {
      label: "Pendientes",
      value: orders.filter((o) => o.status === "pendiente" || o.status === "en_revision").length,
      icon: Clock,
      colorClass: "text-warning-foreground",
      bgClass: "bg-warning/15",
    },
    {
      label: "Aprobados",
      value: orders.filter((o) => o.status === "aprobado").length,
      icon: CheckCircle2,
      colorClass: "text-success",
      bgClass: "bg-success/15",
    },
    {
      label: "Rechazados",
      value: orders.filter((o) => o.status === "rechazado").length,
      icon: XCircle,
      colorClass: "text-destructive",
      bgClass: "bg-destructive/10",
    },
    {
      label: "Entregados",
      value: orders.filter((o) => o.status === "entregado").length,
      icon: Truck,
      colorClass: "text-muted-foreground",
      bgClass: "bg-muted",
    },
  ]

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="flex items-center gap-3 rounded-lg border border-border bg-card p-3.5"
        >
          <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${stat.bgClass}`}>
            <stat.icon className={`h-4 w-4 ${stat.colorClass}`} />
          </div>
          <div className="flex flex-col">
            <span className="text-lg font-semibold leading-none text-foreground">{stat.value}</span>
            <span className="mt-1 text-xs text-muted-foreground">{stat.label}</span>
          </div>
        </div>
      ))}
    </div>
  )
}
