"use client"

import { useState, useMemo } from "react"
import dynamic from "next/dynamic"
import Link from "next/link"
import { Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { MOCK_TICKETS } from "@/lib/tickets-data"
import { TicketStats } from "@/components/tickets/ticket-stats"
import { TicketTable } from "@/components/tickets/ticket-table"

const TicketFilters = dynamic(
  () => import("@/components/tickets/ticket-filters").then((mod) => ({ default: mod.TicketFilters })),
  { ssr: false }
)

export default function TicketsPage() {
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("todos")
  const [typeFilter, setTypeFilter] = useState("todos")
  const [priorityFilter, setPriorityFilter] = useState("todos")

  const filteredTickets = useMemo(() => {
    return MOCK_TICKETS.filter((ticket) => {
      const matchesSearch =
        search === "" ||
        ticket.title.toLowerCase().includes(search.toLowerCase()) ||
        ticket.code.toLowerCase().includes(search.toLowerCase()) ||
        ticket.reporter.toLowerCase().includes(search.toLowerCase())
      
      const matchesStatus = statusFilter === "todos" || ticket.status === statusFilter
      const matchesType = typeFilter === "todos" || ticket.type === typeFilter
      const matchesPriority = priorityFilter === "todos" || ticket.priority === priorityFilter

      return matchesSearch && matchesStatus && matchesType && matchesPriority
    })
  }, [search, statusFilter, typeFilter, priorityFilter])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Tickets de Soporte</h1>
          <p className="text-muted-foreground mt-1">
            Gestiona las solicitudes y problemas tecnicos del equipo
          </p>
        </div>
        <Button asChild>
          <Link href="/tickets/nuevo">
            <Plus className="mr-2 h-4 w-4" />
            Nuevo Ticket
          </Link>
        </Button>
      </div>

      <TicketStats tickets={MOCK_TICKETS} />

      <div className="space-y-4">
        <TicketFilters
          search={search}
          onSearchChange={setSearch}
          statusFilter={statusFilter}
          onStatusChange={setStatusFilter}
          typeFilter={typeFilter}
          onTypeChange={setTypeFilter}
          priorityFilter={priorityFilter}
          onPriorityChange={setPriorityFilter}
        />
        <TicketTable tickets={filteredTickets} />
      </div>
    </div>
  )
}
