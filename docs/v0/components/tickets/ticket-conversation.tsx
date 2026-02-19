"use client"

import { useState } from "react"
import { Send } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import type { TicketMessage } from "@/lib/tickets-data"

function formatTimestamp(timestamp: string) {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return "Justo ahora"
  if (diffMins < 60) return `hace ${diffMins} min`
  if (diffHours < 24) return `hace ${diffHours}h`
  if (diffDays === 1) return "Ayer"
  if (diffDays < 7) return `hace ${diffDays} dias`

  return new Intl.DateTimeFormat("es-ES", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date)
}

export function TicketConversation({ messages }: { messages: TicketMessage[] }) {
  const [newMessage, setNewMessage] = useState("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newMessage.trim()) return
    // TODO: Enviar mensaje
    setNewMessage("")
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-foreground">Conversacion</h2>
      
      <div className="space-y-4">
        {messages.map((message) => (
          <div key={message.id} className="flex gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
              <span className="text-xs font-medium text-primary">
                {message.author.split(" ").map((n) => n[0]).join("")}
              </span>
            </div>
            <div className="flex-1 space-y-1">
              <div className="flex items-baseline gap-2">
                <span className="text-sm font-medium text-foreground">{message.author}</span>
                <span className="text-xs text-muted-foreground">{message.role}</span>
                <span className="text-xs text-muted-foreground">•</span>
                <span className="text-xs text-muted-foreground">{formatTimestamp(message.timestamp)}</span>
              </div>
              <div className="rounded-lg border border-border bg-card p-3">
                <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">{message.content}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        <Textarea
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="Escribe tu respuesta..."
          rows={4}
          className="resize-none"
        />
        <div className="flex justify-end">
          <Button type="submit" disabled={!newMessage.trim()}>
            <Send className="mr-2 h-4 w-4" />
            Enviar respuesta
          </Button>
        </div>
      </form>
    </div>
  )
}
