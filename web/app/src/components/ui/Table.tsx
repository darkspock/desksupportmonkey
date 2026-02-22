import { cn } from '../../lib/cn';

export function Table({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className="relative w-full overflow-x-auto rounded-lg border border-border bg-card">
      <table className={cn('w-full caption-bottom text-sm [&_thead_tr]:border-b [&_thead_tr]:border-border [&_thead_tr]:bg-secondary/40', className)}>
        {children}
      </table>
    </div>
  );
}

export function Th({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <th className={cn('h-10 px-4 py-2 text-left align-middle text-sm font-medium text-foreground whitespace-nowrap', className)}>
      {children}
    </th>
  );
}

export function Td({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <td className={cn('px-4 py-3 text-sm align-middle whitespace-normal break-words', className)}>
      {children}
    </td>
  );
}

export function Tr({ children, className, onClick }: { children: React.ReactNode; className?: string; onClick?: () => void }) {
  return (
    <tr className={cn('border-b border-border transition-colors hover:bg-muted/50', className)} onClick={onClick}>
      {children}
    </tr>
  );
}
