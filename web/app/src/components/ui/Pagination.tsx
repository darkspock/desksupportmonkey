import { useI18n } from '../../lib/i18n';

interface Props {
  page: number;
  pageSize: number;
  total: number;
  onChange: (page: number) => void;
}

export function Pagination({ page, pageSize, total, onChange }: Props) {
  const { t } = useI18n();
  const totalPages = Math.ceil(total / pageSize);
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-between pt-4">
      <span className="text-sm text-muted-foreground">{t('common.total', { count: total })}</span>
      <div className="flex gap-1">
        <button
          disabled={page <= 1}
          onClick={() => onChange(page - 1)}
          className="inline-flex items-center justify-center rounded-md h-8 px-3 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:pointer-events-none disabled:opacity-40"
        >
          {t('common.prev')}
        </button>
        <span className="inline-flex items-center justify-center h-8 px-3 text-sm text-muted-foreground">
          {page} / {totalPages}
        </span>
        <button
          disabled={page >= totalPages}
          onClick={() => onChange(page + 1)}
          className="inline-flex items-center justify-center rounded-md h-8 px-3 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:pointer-events-none disabled:opacity-40"
        >
          {t('common.next')}
        </button>
      </div>
    </div>
  );
}
