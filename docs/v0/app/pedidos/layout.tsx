import { AppShell } from "@/components/app-shell"

export default function PedidosLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <AppShell>{children}</AppShell>
}
