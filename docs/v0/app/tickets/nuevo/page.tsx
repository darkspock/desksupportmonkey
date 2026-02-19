import { NewTicketForm } from "@/components/tickets/new-ticket-form"

export default function NewTicketPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Crear Nuevo Ticket</h1>
        <p className="text-muted-foreground mt-1">
          Describe tu problema o solicitud y el equipo de soporte te ayudara
        </p>
      </div>
      <NewTicketForm />
    </div>
  )
}
