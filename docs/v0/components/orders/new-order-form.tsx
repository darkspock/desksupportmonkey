"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Plus, Trash2, ArrowLeft, Send } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { EQUIPMENT_CATALOG, DEPARTMENTS } from "@/lib/orders-data"

type FormItem = {
  equipmentId: string
  quantity: number
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat("es-ES", {
    style: "currency",
    currency: "EUR",
  }).format(value)
}

export function NewOrderForm() {
  const router = useRouter()
  const [employee, setEmployee] = useState("")
  const [employeeRole, setEmployeeRole] = useState("")
  const [department, setDepartment] = useState("")
  const [priority, setPriority] = useState("")
  const [notes, setNotes] = useState("")
  const [items, setItems] = useState<FormItem[]>([{ equipmentId: "", quantity: 1 }])
  const [submitted, setSubmitted] = useState(false)

  const addItem = () => {
    setItems([...items, { equipmentId: "", quantity: 1 }])
  }

  const removeItem = (index: number) => {
    if (items.length > 1) {
      setItems(items.filter((_, i) => i !== index))
    }
  }

  const updateItem = (index: number, field: keyof FormItem, value: string | number) => {
    const updated = [...items]
    if (field === "quantity") {
      updated[index][field] = Math.max(1, Number(value))
    } else {
      updated[index][field] = value as string
    }
    setItems(updated)
  }

  const getItemPrice = (equipmentId: string) => {
    const equipment = EQUIPMENT_CATALOG.find((e) => e.id === equipmentId)
    return equipment?.unitPrice ?? 0
  }

  const subtotals = items.map((item) => getItemPrice(item.equipmentId) * item.quantity)
  const total = subtotals.reduce((acc, val) => acc + val, 0)

  const isValid =
    employee.trim() !== "" &&
    employeeRole.trim() !== "" &&
    department !== "" &&
    priority !== "" &&
    items.every((item) => item.equipmentId !== "" && item.quantity > 0)

  const handleSubmit = () => {
    if (!isValid) return
    setSubmitted(true)
  }

  if (submitted) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-20">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-success/15">
          <Send className="h-7 w-7 text-success" />
        </div>
        <h2 className="text-xl font-semibold text-foreground">Pedido Enviado</h2>
        <p className="max-w-sm text-center text-sm text-muted-foreground">
          Tu solicitud ha sido enviada correctamente y esta pendiente de aprobacion.
          Recibiras notificaciones sobre el progreso.
        </p>
        <div className="flex gap-3 mt-2">
          <Button variant="outline" onClick={() => router.push("/pedidos")}>
            Ver Pedidos
          </Button>
          <Button onClick={() => { setSubmitted(false); setEmployee(""); setEmployeeRole(""); setDepartment(""); setPriority(""); setNotes(""); setItems([{ equipmentId: "", quantity: 1 }]) }}>
            Nuevo Pedido
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Employee Info */}
      <div className="rounded-lg border border-border bg-card">
        <div className="border-b border-border px-5 py-3.5">
          <h3 className="text-sm font-medium text-foreground">Informacion del Solicitante</h3>
        </div>
        <div className="grid gap-4 p-5 sm:grid-cols-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="employee" className="text-sm text-muted-foreground">
              Nombre del Empleado
            </Label>
            <Input
              id="employee"
              placeholder="Ej: Carlos Martinez"
              value={employee}
              onChange={(e) => setEmployee(e.target.value)}
              className="bg-background"
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="role" className="text-sm text-muted-foreground">
              Cargo
            </Label>
            <Input
              id="role"
              placeholder="Ej: Senior Developer"
              value={employeeRole}
              onChange={(e) => setEmployeeRole(e.target.value)}
              className="bg-background"
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label className="text-sm text-muted-foreground">Departamento</Label>
            <Select value={department} onValueChange={setDepartment}>
              <SelectTrigger className="bg-background">
                <SelectValue placeholder="Seleccionar departamento" />
              </SelectTrigger>
              <SelectContent>
                {DEPARTMENTS.map((dept) => (
                  <SelectItem key={dept} value={dept}>{dept}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label className="text-sm text-muted-foreground">Prioridad</Label>
            <Select value={priority} onValueChange={setPriority}>
              <SelectTrigger className="bg-background">
                <SelectValue placeholder="Seleccionar prioridad" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="alta">Alta</SelectItem>
                <SelectItem value="media">Media</SelectItem>
                <SelectItem value="baja">Baja</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* Equipment Items */}
      <div className="rounded-lg border border-border bg-card">
        <div className="flex items-center justify-between border-b border-border px-5 py-3.5">
          <h3 className="text-sm font-medium text-foreground">Equipamiento Solicitado</h3>
          <Button variant="outline" size="sm" onClick={addItem}>
            <Plus className="mr-1.5 h-3.5 w-3.5" />
            Agregar
          </Button>
        </div>
        <div className="flex flex-col divide-y divide-border">
          {items.map((item, index) => {
            const equipment = EQUIPMENT_CATALOG.find((e) => e.id === item.equipmentId)
            return (
              <div key={index} className="flex items-start gap-3 p-5">
                <div className="flex-1 grid gap-3 sm:grid-cols-[1fr_100px_120px]">
                  <div className="flex flex-col gap-1.5">
                    <Label className="text-xs text-muted-foreground">Producto</Label>
                    <Select
                      value={item.equipmentId}
                      onValueChange={(val) => updateItem(index, "equipmentId", val)}
                    >
                      <SelectTrigger className="bg-background">
                        <SelectValue placeholder="Seleccionar equipo" />
                      </SelectTrigger>
                      <SelectContent>
                        {EQUIPMENT_CATALOG.map((eq) => (
                          <SelectItem key={eq.id} value={eq.id}>
                            <span>{eq.name}</span>
                            <span className="ml-2 text-muted-foreground">
                              {formatCurrency(eq.unitPrice)}
                            </span>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {equipment && (
                      <span className="text-xs text-muted-foreground">
                        Categoria: {equipment.category}
                      </span>
                    )}
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label className="text-xs text-muted-foreground">Cantidad</Label>
                    <Input
                      type="number"
                      min={1}
                      value={item.quantity}
                      onChange={(e) => updateItem(index, "quantity", e.target.value)}
                      className="bg-background"
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label className="text-xs text-muted-foreground">Subtotal</Label>
                    <div className="flex h-9 items-center rounded-md bg-muted px-3 text-sm font-medium text-foreground">
                      {formatCurrency(subtotals[index])}
                    </div>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeItem(index)}
                  disabled={items.length === 1}
                  className="mt-6 text-muted-foreground hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4" />
                  <span className="sr-only">Eliminar item</span>
                </Button>
              </div>
            )
          })}
        </div>
        <div className="flex items-center justify-end border-t border-border px-5 py-3.5">
          <div className="flex items-center gap-3">
            <span className="text-sm text-muted-foreground">Total del pedido:</span>
            <span className="text-lg font-semibold text-foreground">{formatCurrency(total)}</span>
          </div>
        </div>
      </div>

      {/* Notes */}
      <div className="rounded-lg border border-border bg-card">
        <div className="border-b border-border px-5 py-3.5">
          <h3 className="text-sm font-medium text-foreground">Notas Adicionales</h3>
        </div>
        <div className="p-5">
          <Textarea
            placeholder="Justificacion del pedido, informacion adicional..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            className="bg-background resize-none"
          />
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <Button variant="outline" onClick={() => router.push("/pedidos")}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Cancelar
        </Button>
        <Button disabled={!isValid} onClick={handleSubmit}>
          <Send className="mr-2 h-4 w-4" />
          Enviar Solicitud
        </Button>
      </div>
    </div>
  )
}
