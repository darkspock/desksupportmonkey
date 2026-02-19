"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Monitor, Wifi, Package, GraduationCap } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { APPOINTMENT_TYPE_CONFIG, type AppointmentType } from "@/lib/appointments-data"

const TYPE_ICONS = {
  soporte_presencial: Monitor,
  soporte_remoto: Wifi,
  instalacion: Package,
  formacion: GraduationCap,
}

export function NewAppointmentForm() {
  const router = useRouter()
  const [selectedType, setSelectedType] = useState<AppointmentType | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setIsSubmitting(true)

    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000))

    router.push("/citas")
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-6">
      {/* Type Selection */}
      <div className="flex flex-col gap-3">
        <Label className="text-base font-semibold">Tipo de cita</Label>
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
          {(Object.keys(APPOINTMENT_TYPE_CONFIG) as AppointmentType[]).map((type) => {
            const config = APPOINTMENT_TYPE_CONFIG[type]
            const Icon = TYPE_ICONS[type]
            const isSelected = selectedType === type

            return (
              <Card
                key={type}
                className={cn(
                  "relative cursor-pointer border-2 p-4 transition-all hover:border-primary/50",
                  isSelected ? "border-primary bg-primary/5" : "border-border"
                )}
                onClick={() => setSelectedType(type)}
              >
                <div className="flex flex-col items-center text-center gap-3">
                  <div
                    className={cn(
                      "flex h-12 w-12 items-center justify-center rounded-lg transition-colors",
                      isSelected ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                    )}
                  >
                    <Icon className="h-6 w-6" />
                  </div>
                  <div>
                    <p className={cn("text-sm font-medium", isSelected ? "text-primary" : "text-foreground")}>
                      {config.label}
                    </p>
                  </div>
                </div>
              </Card>
            )
          })}
        </div>
      </div>

      {selectedType && (
        <>
          {/* Date and Time */}
          <div className="grid gap-4 md:grid-cols-3">
            <div className="flex flex-col gap-2">
              <Label htmlFor="date">Fecha</Label>
              <Input id="date" type="date" required />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="startTime">Hora inicio</Label>
              <Input id="startTime" type="time" required />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="endTime">Hora fin</Label>
              <Input id="endTime" type="time" required />
            </div>
          </div>

          {/* User Information */}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="flex flex-col gap-2">
              <Label htmlFor="user">Usuario</Label>
              <Input id="user" placeholder="Nombre del usuario" required />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="userEmail">Email del usuario</Label>
              <Input id="userEmail" type="email" placeholder="usuario@company.com" required />
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="flex flex-col gap-2">
              <Label htmlFor="department">Departamento</Label>
              <Input id="department" placeholder="Ingenieria, Marketing, etc." required />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="technician">Tecnico asignado</Label>
              <Input id="technician" placeholder="Nombre del tecnico" required />
            </div>
          </div>

          {/* Location (for onsite) */}
          {(selectedType === "soporte_presencial" || selectedType === "instalacion" || selectedType === "formacion") && (
            <div className="flex flex-col gap-2">
              <Label htmlFor="location">Ubicacion</Label>
              <Input id="location" placeholder="Oficina - Planta 3, Puesto 32" />
            </div>
          )}

          {/* Title and Notes */}
          <div className="flex flex-col gap-2">
            <Label htmlFor="title">Titulo de la cita</Label>
            <Input id="title" placeholder="Breve descripcion de la cita" required />
          </div>

          <div className="flex flex-col gap-2">
            <Label htmlFor="notes">Notas adicionales</Label>
            <Textarea
              id="notes"
              placeholder="Detalles adicionales sobre la cita..."
              rows={4}
              className="resize-none"
            />
          </div>

          {/* Actions */}
          <div className="flex gap-3 justify-end">
            <Button type="button" variant="outline" onClick={() => router.back()}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Creando..." : "Crear Cita"}
            </Button>
          </div>
        </>
      )}

      {!selectedType && (
        <p className="text-center text-sm text-muted-foreground py-8">Selecciona un tipo de cita para continuar</p>
      )}
    </form>
  )
}
