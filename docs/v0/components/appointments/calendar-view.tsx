"use client"

import { useState } from "react"
import Link from "next/link"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import {
  getMonthDays,
  formatDateToISO,
  getAppointmentsByDate,
  APPOINTMENT_TYPE_CONFIG,
  type Appointment,
} from "@/lib/appointments-data"

const MONTH_NAMES = [
  "Enero",
  "Febrero",
  "Marzo",
  "Abril",
  "Mayo",
  "Junio",
  "Julio",
  "Agosto",
  "Septiembre",
  "Octubre",
  "Noviembre",
  "Diciembre",
]

const DAY_NAMES = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]

export function CalendarView({ appointments }: { appointments: Appointment[] }) {
  const today = new Date()
  const [currentDate, setCurrentDate] = useState(new Date(today.getFullYear(), today.getMonth(), 1))

  const year = currentDate.getFullYear()
  const month = currentDate.getMonth()
  const monthDays = getMonthDays(year, month)

  const goToPrevMonth = () => {
    setCurrentDate(new Date(year, month - 1, 1))
  }

  const goToNextMonth = () => {
    setCurrentDate(new Date(year, month + 1, 1))
  }

  const goToToday = () => {
    setCurrentDate(new Date(today.getFullYear(), today.getMonth(), 1))
  }

  const isToday = (date: Date) => {
    return (
      date.getDate() === today.getDate() &&
      date.getMonth() === today.getMonth() &&
      date.getFullYear() === today.getFullYear()
    )
  }

  const isCurrentMonth = (date: Date) => {
    return date.getMonth() === month
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Calendar Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-semibold text-foreground">
            {MONTH_NAMES[month]} {year}
          </h2>
          <Button variant="outline" size="sm" onClick={goToToday}>
            Hoy
          </Button>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon" onClick={goToPrevMonth}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon" onClick={goToNextMonth}>
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Calendar Grid */}
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        {/* Day Names Header */}
        <div className="grid grid-cols-7 border-b border-border bg-muted/30">
          {DAY_NAMES.map((day) => (
            <div key={day} className="px-2 py-3 text-center text-xs font-medium text-muted-foreground">
              {day}
            </div>
          ))}
        </div>

        {/* Calendar Days */}
        <div className="grid grid-cols-7">
          {monthDays.map((date, index) => {
            const dateStr = formatDateToISO(date)
            const dayAppointments = getAppointmentsByDate(dateStr)
            const isCurrentMonthDay = isCurrentMonth(date)
            const isTodayDay = isToday(date)

            return (
              <div
                key={index}
                className={cn(
                  "min-h-[120px] border-r border-b border-border p-2 transition-colors hover:bg-accent/50",
                  !isCurrentMonthDay && "bg-muted/20",
                  index % 7 === 6 && "border-r-0"
                )}
              >
                <div className="flex flex-col h-full">
                  <div
                    className={cn(
                      "flex h-7 w-7 items-center justify-center rounded-full text-sm font-medium mb-1",
                      isTodayDay
                        ? "bg-primary text-primary-foreground"
                        : isCurrentMonthDay
                          ? "text-foreground"
                          : "text-muted-foreground"
                    )}
                  >
                    {date.getDate()}
                  </div>

                  <div className="flex flex-col gap-1 overflow-y-auto flex-1">
                    {dayAppointments.slice(0, 3).map((apt) => {
                      const typeConfig = APPOINTMENT_TYPE_CONFIG[apt.type]
                      return (
                        <Link
                          key={apt.id}
                          href={`/citas/${apt.id}`}
                          className="group rounded px-1.5 py-1 text-xs hover:ring-2 hover:ring-primary/20 transition-all"
                          style={{ backgroundColor: typeConfig.color + "15" }}
                        >
                          <div className="flex items-center gap-1">
                            <div
                              className="h-2 w-2 rounded-full flex-shrink-0"
                              style={{ backgroundColor: typeConfig.color }}
                            />
                            <span className="font-medium truncate" style={{ color: typeConfig.color }}>
                              {apt.startTime}
                            </span>
                          </div>
                          <p className="truncate text-foreground/80 leading-tight mt-0.5">{apt.title}</p>
                        </Link>
                      )
                    })}
                    {dayAppointments.length > 3 && (
                      <button className="text-xs text-muted-foreground hover:text-foreground px-1.5 py-0.5 text-left">
                        +{dayAppointments.length - 3} mas
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
