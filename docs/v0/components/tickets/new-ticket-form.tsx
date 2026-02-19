"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { AlertCircle, CheckCircle2, Laptop, UserPlus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { DEPARTMENTS } from "@/lib/orders-data"
import { TICKET_TYPE_CONFIG, type TicketType } from "@/lib/tickets-data"

const TYPE_ICON_MAP = {
  equipo_no_funciona: AlertCircle,
  nuevo_ordenador: Laptop,
  onboarding: UserPlus,
}

export function NewTicketForm() {
  const router = useRouter()
  const [submitted, setSubmitted] = useState(false)
  const [formData, setFormData] = useState({
    title: "",
    type: "" as TicketType | "",
    priority: "media",
    reporter: "",
    reporterEmail: "",
    department: "",
    description: "",
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitted(true)
    setTimeout(() => {
      router.push("/tickets")
    }, 2000)
  }

  if (submitted) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-border bg-card p-12">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-success/15 mb-4">
          <CheckCircle2 className="h-8 w-8 text-success" />
        </div>
        <h3 className="text-xl font-semibold text-foreground mb-2">Ticket creado correctamente</h3>
        <p className="text-sm text-muted-foreground text-center max-w-md">
          Tu solicitud ha sido enviada al equipo de soporte. Te notificaremos cuando haya actualizaciones.
        </p>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="rounded-lg border border-border bg-card p-6 space-y-6">
        <div>
          <h2 className="text-lg font-semibold text-foreground mb-4">Tipo de solicitud</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {(Object.entries(TICKET_TYPE_CONFIG) as [TicketType, typeof TICKET_TYPE_CONFIG[TicketType]][]).map(([key, config]) => {
              const Icon = TYPE_ICON_MAP[key]
              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => setFormData({ ...formData, type: key })}
                  className={`flex flex-col items-start gap-3 rounded-lg border p-4 text-left transition-all hover:border-primary ${
                    formData.type === key ? "border-primary bg-primary/5" : "border-border"
                  }`}
                >
                  <div className={`flex h-10 w-10 items-center justify-center rounded-md ${
                    formData.type === key ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                  }`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="font-medium text-sm text-foreground">{config.label}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">{config.description}</p>
                  </div>
                </button>
              )
            })}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="reporter">Tu nombre *</Label>
            <Input
              id="reporter"
              value={formData.reporter}
              onChange={(e) => setFormData({ ...formData, reporter: e.target.value })}
              placeholder="Nombre completo"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="reporterEmail">Email corporativo *</Label>
            <Input
              id="reporterEmail"
              type="email"
              value={formData.reporterEmail}
              onChange={(e) => setFormData({ ...formData, reporterEmail: e.target.value })}
              placeholder="tu.email@company.com"
              required
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="department">Departamento *</Label>
            <Select value={formData.department} onValueChange={(value) => setFormData({ ...formData, department: value })}>
              <SelectTrigger>
                <SelectValue placeholder="Selecciona departamento" />
              </SelectTrigger>
              <SelectContent>
                {DEPARTMENTS.map((dept) => (
                  <SelectItem key={dept} value={dept}>
                    {dept}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="priority">Prioridad *</Label>
            <Select value={formData.priority} onValueChange={(value) => setFormData({ ...formData, priority: value })}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="critica">Critica - Trabajo bloqueado</SelectItem>
                <SelectItem value="alta">Alta - Urgente</SelectItem>
                <SelectItem value="media">Media - Normal</SelectItem>
                <SelectItem value="baja">Baja - Puede esperar</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="title">Titulo del problema *</Label>
          <Input
            id="title"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            placeholder="Describe brevemente el problema"
            required
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Descripcion detallada *</Label>
          <Textarea
            id="description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="Describe el problema en detalle. Incluye: que paso, cuando empezo, que has intentado hacer, mensajes de error, etc."
            rows={6}
            className="resize-none"
            required
          />
          <p className="text-xs text-muted-foreground">
            Cuanto mas detallada sea la descripcion, mas rapido podremos ayudarte.
          </p>
        </div>
      </div>

      <div className="flex items-center justify-end gap-3">
        <Button type="button" variant="outline" onClick={() => router.push("/tickets")}>
          Cancelar
        </Button>
        <Button type="submit" disabled={!formData.type || !formData.title || !formData.description}>
          Enviar solicitud
        </Button>
      </div>
    </form>
  )
}
