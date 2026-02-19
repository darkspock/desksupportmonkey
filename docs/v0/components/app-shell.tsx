"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Package, ClipboardList, Plus, TicketIcon, MessageSquarePlus, Calendar, CalendarPlus } from "lucide-react"
import { cn } from "@/lib/utils"

const NAV_ITEMS = [
  { href: "/pedidos", label: "Pedidos", icon: ClipboardList },
  { href: "/pedidos/nuevo", label: "Nuevo Pedido", icon: Plus },
  { href: "/tickets", label: "Tickets", icon: TicketIcon },
  { href: "/tickets/nuevo", label: "Nuevo Ticket", icon: MessageSquarePlus },
  { href: "/citas", label: "Calendario", icon: Calendar },
  { href: "/citas/nueva", label: "Nueva Cita", icon: CalendarPlus },
]

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="sticky top-0 z-40 border-b border-border bg-card">
        <div className="mx-auto flex h-14 max-w-7xl items-center px-4 lg:px-6">
          <Link href="/pedidos" className="flex items-center gap-2.5 mr-8">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
              <Package className="h-4 w-4 text-primary-foreground" />
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-semibold leading-none text-foreground">EquipManager</span>
              <span className="text-[10px] text-muted-foreground leading-none mt-0.5">Gestion IT</span>
            </div>
          </Link>
          <nav className="flex items-center gap-1">
            {NAV_ITEMS.map((item) => {
              const isActive = pathname === item.href || (item.href !== "/pedidos" && pathname.startsWith(item.href))
              const isExactActive = pathname === item.href
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                    isExactActive
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:bg-accent hover:text-foreground"
                  )}
                >
                  <item.icon className="h-4 w-4" />
                  <span className="hidden sm:inline">{item.label}</span>
                </Link>
              )
            })}
          </nav>
          <div className="ml-auto flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                <span className="text-xs font-medium text-primary">AM</span>
              </div>
              <div className="hidden md:flex flex-col">
                <span className="text-sm font-medium text-foreground leading-none">Admin</span>
                <span className="text-[11px] text-muted-foreground leading-none mt-0.5">Gestionar</span>
              </div>
            </div>
          </div>
        </div>
      </header>
      <main className="flex-1">
        <div className="mx-auto max-w-7xl px-4 py-6 lg:px-6">
          {children}
        </div>
      </main>
    </div>
  )
}
