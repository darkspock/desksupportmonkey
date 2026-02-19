"use client"

import Link from "next/link"
import { CalendarPlus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { MOCK_APPOINTMENTS } from "@/lib/appointments-data"
import { AppointmentStats } from "@/components/appointments/appointment-stats"
import { CalendarView } from "@/components/appointments/calendar-view"

export default function CitasPage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-foreground text-balance">Calendario de Citas</h1>
          <p className="text-sm text-muted-foreground mt-1">Gestiona las citas de soporte tecnico</p>
        </div>
        <Button asChild>
          <Link href="/citas/nueva">
            <CalendarPlus className="h-4 w-4 mr-2" />
            Nueva Cita
          </Link>
        </Button>
      </div>

      <AppointmentStats appointments={MOCK_APPOINTMENTS} />

      <CalendarView appointments={MOCK_APPOINTMENTS} />
    </div>
  )
}
