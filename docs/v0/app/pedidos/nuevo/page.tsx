import { NewOrderForm } from "@/components/orders/new-order-form"

export default function NuevoPedidoPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground text-balance">
          Nuevo Pedido de Equipamiento
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Completa el formulario para solicitar equipamiento para un empleado
        </p>
      </div>
      <NewOrderForm />
    </div>
  )
}
