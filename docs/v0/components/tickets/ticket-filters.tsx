"use client"

import { Search } from "lucide-react"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { DEPARTMENTS } from "@/lib/orders-data"

type TicketFiltersProps = {
  search: string
  onSearchChange: (value: string) => void
  statusFilter: string
  onStatusChange: (value: string) => void
  typeFilter: string
  onTypeChange: (value: string) => void
  priorityFilter: string
  onPriorityChange: (value: string) => void
}

export function TicketFilters({
  search,
  onSearchChange,
  statusFilter,
  onStatusChange,
  typeFilter,
  onTypeChange,
  priorityFilter,
  onPriorityChange,
}: TicketFiltersProps) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Buscar tickets..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-9"
        />
      </div>
      <Select value={statusFilter} onValueChange={onStatusChange}>
        <SelectTrigger className="w-full sm:w-[160px]">
          <SelectValue placeholder="Estado" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="todos">Todos los estados</SelectItem>
          <SelectItem value="abierto">Abierto</SelectItem>
          <SelectItem value="en_progreso">En progreso</SelectItem>
          <SelectItem value="esperando_respuesta">Esperando respuesta</SelectItem>
          <SelectItem value="resuelto">Resuelto</SelectItem>
          <SelectItem value="cerrado">Cerrado</SelectItem>
        </SelectContent>
      </Select>
      <Select value={typeFilter} onValueChange={onTypeChange}>
        <SelectTrigger className="w-full sm:w-[200px]">
          <SelectValue placeholder="Tipo" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="todos">Todos los tipos</SelectItem>
          <SelectItem value="equipo_no_funciona">Mi ordenador no funciona</SelectItem>
          <SelectItem value="nuevo_ordenador">Nuevo ordenador</SelectItem>
          <SelectItem value="onboarding">Onboarding</SelectItem>
        </SelectContent>
      </Select>
      <Select value={priorityFilter} onValueChange={onPriorityChange}>
        <SelectTrigger className="w-full sm:w-[140px]">
          <SelectValue placeholder="Prioridad" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="todos">Todas</SelectItem>
          <SelectItem value="critica">Critica</SelectItem>
          <SelectItem value="alta">Alta</SelectItem>
          <SelectItem value="media">Media</SelectItem>
          <SelectItem value="baja">Baja</SelectItem>
        </SelectContent>
      </Select>
    </div>
  )
}
