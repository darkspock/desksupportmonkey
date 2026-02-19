"use client"

import { Check, Clock, X, CircleDot } from "lucide-react"
import { cn } from "@/lib/utils"
import type { ApprovalStep } from "@/lib/orders-data"

const STEP_ICONS = {
  completado: Check,
  actual: CircleDot,
  pendiente: Clock,
  rechazado: X,
}

const STEP_STYLES = {
  completado: {
    iconBg: "bg-success/15",
    iconColor: "text-success",
    lineColor: "bg-success/40",
    labelColor: "text-foreground",
  },
  actual: {
    iconBg: "bg-primary/15",
    iconColor: "text-primary",
    lineColor: "bg-border",
    labelColor: "text-primary",
  },
  pendiente: {
    iconBg: "bg-muted",
    iconColor: "text-muted-foreground",
    lineColor: "bg-border",
    labelColor: "text-muted-foreground",
  },
  rechazado: {
    iconBg: "bg-destructive/10",
    iconColor: "text-destructive",
    lineColor: "bg-destructive/30",
    labelColor: "text-destructive",
  },
}

function formatDate(dateStr: string) {
  return new Intl.DateTimeFormat("es-ES", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(dateStr))
}

export function ApprovalTimeline({ steps }: { steps: ApprovalStep[] }) {
  return (
    <div className="flex flex-col">
      {steps.map((step, index) => {
        const isLast = index === steps.length - 1
        const style = STEP_STYLES[step.status]
        const Icon = STEP_ICONS[step.status]

        return (
          <div key={step.id} className="flex gap-4">
            {/* Timeline line & icon */}
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  "flex h-9 w-9 shrink-0 items-center justify-center rounded-full transition-colors",
                  style.iconBg,
                  step.status === "actual" && "ring-4 ring-primary/10"
                )}
              >
                <Icon className={cn("h-4 w-4", style.iconColor)} />
              </div>
              {!isLast && (
                <div className={cn("w-0.5 flex-1 min-h-8", style.lineColor)} />
              )}
            </div>

            {/* Content */}
            <div className={cn("flex-1 pb-6", isLast && "pb-0")}>
              <div className="flex flex-col gap-0.5 -mt-0.5">
                <span className={cn("text-sm font-medium", style.labelColor)}>
                  {step.label}
                </span>
                <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5">
                  <span className="text-sm text-foreground">{step.approver}</span>
                  <span className="text-xs text-muted-foreground">{step.role}</span>
                </div>
                {step.date && (
                  <span className="text-xs text-muted-foreground mt-0.5">
                    {formatDate(step.date)}
                  </span>
                )}
                {step.comment && (
                  <div className="mt-2 rounded-md bg-muted/50 border border-border px-3 py-2">
                    <p className="text-sm text-foreground leading-relaxed">
                      {step.comment}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
