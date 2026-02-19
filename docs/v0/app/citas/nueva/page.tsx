import { NewAppointmentForm } from "@/components/appointments/new-appointment-form"

export default function NuevaCitaPage() {
  return (
    <div className="max-w-4xl">
      <div className="mb-6">
        <h1 className="text-3xl font-semibold text-foreground text-balance">Nueva Cita de Soporte</h1>
        <p className="text-sm text-muted-foreground mt-1">Programa una cita con el equipo de IT</p>
      </div>

      <NewAppointmentForm />
    </div>
  )
}
