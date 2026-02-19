import { notFound } from "next/navigation"
import { MOCK_APPOINTMENTS } from "@/lib/appointments-data"
import { AppointmentDetail } from "@/components/appointments/appointment-detail"

export default function CitaDetailPage({ params }: { params: { id: string } }) {
  const appointment = MOCK_APPOINTMENTS.find((a) => a.id === params.id)

  if (!appointment) {
    notFound()
  }

  return <AppointmentDetail appointment={appointment} />
}
