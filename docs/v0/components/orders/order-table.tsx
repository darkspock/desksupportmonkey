"use client"

import Link from "next/link"
import { ClipboardCheck, Copy, Eye, MoreVertical, PackageCheck, Printer, RotateCcw, Trash2 } from "lucide-react"
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
import type { Order, OrderStatus } from "@/lib/orders-data"
import { STATUS_CONFIG, PRIORITY_CONFIG } from "@/lib/orders-data"

function formatCurrency(value: number) {
  return new Intl.NumberFormat("es-ES", {
    style: "currency",
    currency: "EUR",
  }).format(value)
}

function formatDate(dateStr: string) {
  return new Intl.DateTimeFormat("es-ES", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(dateStr))
}

const NEXT_ACTION: Record<
  OrderStatus,
  { label: string; icon: React.ElementType; variant: "default" | "outline" | "secondary" | "ghost"; href?: (id: string) => string } | null
> = {
  pendiente: {
    label: "Revisar",
    icon: ClipboardCheck,
    variant: "default",
    href: (id) => `/pedidos/${id}`,
  },
  en_revision: {
    label: "Revisar",
    icon: ClipboardCheck,
    variant: "default",
    href: (id) => `/pedidos/${id}`,
  },
  aprobado: {
    label: "Marcar entregado",
    icon: PackageCheck,
    variant: "outline",
  },
  rechazado: {
    label: "Reenviar",
    icon: RotateCcw,
    variant: "outline",
  },
  entregado: null,
}

export function OrderTable({ orders }: { orders: Order[] }) {
  if (orders.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-card py-16">
        <p className="text-sm text-muted-foreground">No se encontraron pedidos</p>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-border bg-card overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead className="pl-4">Codigo</TableHead>
            <TableHead>Empleado</TableHead>
            <TableHead className="hidden md:table-cell">Departamento</TableHead>
            <TableHead className="hidden sm:table-cell">Fecha</TableHead>
            <TableHead>Estado</TableHead>
            <TableHead className="hidden lg:table-cell">Prioridad</TableHead>
            <TableHead className="text-right">Total</TableHead>
            <TableHead className="w-24 pr-4">
              <span className="sr-only">Acciones</span>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {orders.map((order) => {
            const statusConfig = STATUS_CONFIG[order.status]
            const priorityConfig = PRIORITY_CONFIG[order.priority]
            const nextAction = NEXT_ACTION[order.status]

            return (
              <TableRow key={order.id} className="group">
                <TableCell className="pl-4">
                  <Link href={`/pedidos/${order.id}`} className="font-mono text-sm font-medium text-foreground hover:text-primary transition-colors">
                    {order.code}
                  </Link>
                </TableCell>
                <TableCell>
                  <div className="flex flex-col">
                    <span className="text-sm font-medium text-foreground">{order.employee}</span>
                    <span className="text-xs text-muted-foreground">{order.employeeRole}</span>
                  </div>
                </TableCell>
                <TableCell className="hidden md:table-cell">
                  <span className="text-sm text-muted-foreground">{order.department}</span>
                </TableCell>
                <TableCell className="hidden sm:table-cell">
                  <span className="text-sm text-muted-foreground">{formatDate(order.date)}</span>
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
                <TableCell className="text-right">
                  <span className="text-sm font-medium text-foreground">{formatCurrency(order.total)}</span>
                </TableCell>
                <TableCell className="pr-4">
                  <div className="flex items-center justify-end gap-1">
                    <Tooltip>
                      <TooltipTrigger asChild>
                        {nextAction ? (
                          nextAction.href ? (
                            <Button variant={nextAction.variant} size="icon" className="h-8 w-8" asChild>
                              <Link href={nextAction.href(order.id)}>
                                <nextAction.icon className="h-4 w-4" />
                                <span className="sr-only">{nextAction.label}</span>
                              </Link>
                            </Button>
                          ) : (
                            <Button variant={nextAction.variant} size="icon" className="h-8 w-8">
                              <nextAction.icon className="h-4 w-4" />
                              <span className="sr-only">{nextAction.label}</span>
                            </Button>
                          )
                        ) : (
                          <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground" asChild>
                            <Link href={`/pedidos/${order.id}`}>
                              <Eye className="h-4 w-4" />
                              <span className="sr-only">Ver</span>
                            </Link>
                          </Button>
                        )}
                      </TooltipTrigger>
                      <TooltipContent side="left">
                        {nextAction ? nextAction.label : "Ver pedido"}
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
                          <Link href={`/pedidos/${order.id}`} className="gap-2">
                            <Eye className="h-4 w-4" />
                            Ver detalle
                          </Link>
                        </DropdownMenuItem>
                        <DropdownMenuItem className="gap-2">
                          <Copy className="h-4 w-4" />
                          Duplicar pedido
                        </DropdownMenuItem>
                        <DropdownMenuItem className="gap-2">
                          <Printer className="h-4 w-4" />
                          Imprimir
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem className="gap-2 text-destructive focus:text-destructive">
                          <Trash2 className="h-4 w-4" />
                          Cancelar pedido
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
