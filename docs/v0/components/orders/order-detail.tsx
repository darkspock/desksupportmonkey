"use client"

import Link from "next/link"
import { ArrowLeft, User, Building2, Calendar, FileText, Hash } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import type { Order } from "@/lib/orders-data"
import { STATUS_CONFIG, PRIORITY_CONFIG } from "@/lib/orders-data"
import { ApprovalTimeline } from "./approval-timeline"

function formatCurrency(value: number) {
  return new Intl.NumberFormat("es-ES", {
    style: "currency",
    currency: "EUR",
  }).format(value)
}

function formatDate(dateStr: string) {
  return new Intl.DateTimeFormat("es-ES", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  }).format(new Date(dateStr))
}

export function OrderDetail({ order }: { order: Order }) {
  const statusConfig = STATUS_CONFIG[order.status]
  const priorityConfig = PRIORITY_CONFIG[order.priority]

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <Link href="/pedidos">
            <Button variant="outline" size="sm">
              <ArrowLeft className="mr-1.5 h-3.5 w-3.5" />
              Volver
            </Button>
          </Link>
          <div className="flex flex-col">
            <div className="flex items-center gap-2.5">
              <h1 className="text-xl font-semibold text-foreground">{order.code}</h1>
              <Badge variant="outline" className={statusConfig.className}>
                {statusConfig.label}
              </Badge>
              <Badge variant="outline" className={priorityConfig.className}>
                {priorityConfig.label}
              </Badge>
            </div>
          </div>
        </div>
        {(order.status === "pendiente" || order.status === "en_revision") && (
          <div className="flex gap-2">
            <Button variant="outline" className="text-destructive border-destructive/30 hover:bg-destructive/10">
              Rechazar
            </Button>
            <Button>
              Aprobar
            </Button>
          </div>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
        {/* Left Column */}
        <div className="flex flex-col gap-6">
          {/* Employee Info Card */}
          <div className="rounded-lg border border-border bg-card">
            <div className="border-b border-border px-5 py-3.5">
              <h3 className="text-sm font-medium text-foreground">Informacion del Pedido</h3>
            </div>
            <div className="grid gap-4 p-5 sm:grid-cols-2">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                  <User className="h-4 w-4 text-primary" />
                </div>
                <div className="flex flex-col">
                  <span className="text-xs text-muted-foreground">Solicitante</span>
                  <span className="text-sm font-medium text-foreground">{order.employee}</span>
                  <span className="text-xs text-muted-foreground">{order.employeeRole}</span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                  <Building2 className="h-4 w-4 text-primary" />
                </div>
                <div className="flex flex-col">
                  <span className="text-xs text-muted-foreground">Departamento</span>
                  <span className="text-sm font-medium text-foreground">{order.department}</span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                  <Calendar className="h-4 w-4 text-primary" />
                </div>
                <div className="flex flex-col">
                  <span className="text-xs text-muted-foreground">Fecha de Solicitud</span>
                  <span className="text-sm font-medium text-foreground">{formatDate(order.date)}</span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                  <Hash className="h-4 w-4 text-primary" />
                </div>
                <div className="flex flex-col">
                  <span className="text-xs text-muted-foreground">Articulos</span>
                  <span className="text-sm font-medium text-foreground">
                    {order.items.reduce((acc, i) => acc + i.quantity, 0)} unidad(es)
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Items Table */}
          <div className="rounded-lg border border-border bg-card overflow-hidden">
            <div className="border-b border-border px-5 py-3.5">
              <h3 className="text-sm font-medium text-foreground">Detalle de Equipamiento</h3>
            </div>
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead className="pl-5">Producto</TableHead>
                  <TableHead>Categoria</TableHead>
                  <TableHead className="text-right">Precio Ud.</TableHead>
                  <TableHead className="text-right">Cant.</TableHead>
                  <TableHead className="text-right pr-5">Subtotal</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {order.items.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell className="pl-5">
                      <span className="text-sm font-medium text-foreground">{item.name}</span>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-muted-foreground">{item.category}</span>
                    </TableCell>
                    <TableCell className="text-right">
                      <span className="text-sm text-muted-foreground">{formatCurrency(item.unitPrice)}</span>
                    </TableCell>
                    <TableCell className="text-right">
                      <span className="text-sm text-foreground">{item.quantity}</span>
                    </TableCell>
                    <TableCell className="text-right pr-5">
                      <span className="text-sm font-medium text-foreground">
                        {formatCurrency(item.unitPrice * item.quantity)}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <div className="flex items-center justify-end border-t border-border px-5 py-3.5">
              <div className="flex items-center gap-3">
                <span className="text-sm text-muted-foreground">Total:</span>
                <span className="text-lg font-semibold text-foreground">{formatCurrency(order.total)}</span>
              </div>
            </div>
          </div>

          {/* Notes */}
          {order.notes && (
            <div className="rounded-lg border border-border bg-card">
              <div className="border-b border-border px-5 py-3.5">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <h3 className="text-sm font-medium text-foreground">Notas</h3>
                </div>
              </div>
              <div className="px-5 py-4">
                <p className="text-sm text-foreground leading-relaxed">{order.notes}</p>
              </div>
            </div>
          )}
        </div>

        {/* Right Column - Approval Flow */}
        <div className="flex flex-col gap-6">
          <div className="rounded-lg border border-border bg-card">
            <div className="border-b border-border px-5 py-3.5">
              <h3 className="text-sm font-medium text-foreground">Flujo de Aprobacion</h3>
              <p className="mt-0.5 text-xs text-muted-foreground">
                {order.approvalSteps.filter((s) => s.status === "completado").length} de{" "}
                {order.approvalSteps.length} pasos completados
              </p>
            </div>
            {/* Progress bar */}
            <div className="px-5 pt-4">
              <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                <div
                  className="h-full rounded-full bg-primary transition-all duration-500"
                  style={{
                    width: `${
                      (order.approvalSteps.filter((s) => s.status === "completado").length /
                        order.approvalSteps.length) *
                      100
                    }%`,
                  }}
                />
              </div>
            </div>
            <Separator className="mt-4" />
            <div className="p-5">
              <ApprovalTimeline steps={order.approvalSteps} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
