import { cn } from '../../lib/cn';

export function Card({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div
      className={cn(
        'rounded-xl border border-border bg-card text-card-foreground shadow-sm p-5',
        className,
      )}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn('border-b border-border px-5 py-3.5', className)}>
      {children}
    </div>
  );
}

export function CardBody({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn('p-5', className)}>
      {children}
    </div>
  );
}

export function StatCard({
  label,
  value,
  sub,
  icon,
  colorClass = 'text-primary',
  bgClass = 'bg-primary/10',
}: {
  label: string;
  value: string | number;
  sub?: string;
  icon?: React.ReactNode;
  colorClass?: string;
  bgClass?: string;
}) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-border bg-card p-3.5">
      {icon ? (
        <div className={cn('flex h-9 w-9 shrink-0 items-center justify-center rounded-lg', bgClass)}>
          <span className={colorClass}>{icon}</span>
        </div>
      ) : null}
      <div className="flex flex-col">
        <span className="text-lg font-semibold leading-none text-foreground">{value}</span>
        <span className="mt-1 text-xs text-muted-foreground">{label}</span>
        {sub && <span className="text-[11px] text-muted-foreground">{sub}</span>}
      </div>
    </div>
  );
}
