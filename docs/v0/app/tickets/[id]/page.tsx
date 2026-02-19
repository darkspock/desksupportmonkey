import { notFound } from "next/navigation"
import { MOCK_TICKETS } from "@/lib/tickets-data"
import { TicketDetail } from "@/components/tickets/ticket-detail"

export default async function TicketDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const ticket = MOCK_TICKETS.find((t) => t.id === id)

  if (!ticket) {
    notFound()
  }

  return <TicketDetail ticket={ticket} />
}
