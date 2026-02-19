"use client"

import { useState, useMemo } from "react"
import dynamic from "next/dynamic"
import Link from "next/link"
import { Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { MOCK_ORDERS } from "@/lib/orders-data"
import { OrderStats } from "@/components/orders/order-stats"
import { OrderTable } from "@/components/orders/order-table"

const OrderFilters = dynamic(
  () => import("@/components/orders/order-filters").then((mod) => ({ default: mod.OrderFilters })),
  { ssr: false }
)

export default function PedidosPage() {
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("todos")
  const [departmentFilter, setDepartmentFilter] = useState("todos")

  const filteredOrders = useMemo(() => {
    return MOCK_ORDERS.filter((order) => {
      const matchesSearch =
        search === "" ||
        order.code.toLowerCase().includes(search.toLowerCase()) ||
        order.employee.toLowerCase().includes(search.toLowerCase()) ||
        order.department.toLowerCase().includes(search.toLowerCase())

      const matchesStatus = statusFilter === "todos" || order.status === statusFilter
      const matchesDepartment = departmentFilter === "todos" || order.department === departmentFilter

      return matchesSearch && matchesStatus && matchesDepartment
    })
  }, [search, statusFilter, departmentFilter])

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground text-balance">
            Pedidos de Equipamiento
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Gestiona las solicitudes de compra de equipamiento para empleados
          </p>
        </div>
        <Link href="/pedidos/nuevo">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Nuevo Pedido
          </Button>
        </Link>
      </div>

      <OrderStats orders={MOCK_ORDERS} />

      <OrderFilters
        search={search}
        onSearchChange={setSearch}
        statusFilter={statusFilter}
        onStatusFilterChange={setStatusFilter}
        departmentFilter={departmentFilter}
        onDepartmentFilterChange={setDepartmentFilter}
      />

      <OrderTable orders={filteredOrders} />
    </div>
  )
}
