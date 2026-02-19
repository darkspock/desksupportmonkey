import { notFound } from "next/navigation"
import { MOCK_ORDERS } from "@/lib/orders-data"
import { OrderDetail } from "@/components/orders/order-detail"

export default async function PedidoDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const order = MOCK_ORDERS.find((o) => o.id === id)

  if (!order) {
    notFound()
  }

  return <OrderDetail order={order} />
}
