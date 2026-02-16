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
      <span className="text-sm text-gray-500">{t('common.total', { count: total })}</span>
      <div className="flex gap-1">
        <button
          disabled={page <= 1}
          onClick={() => onChange(page - 1)}
          className="px-3 py-1 text-sm rounded border disabled:opacity-40 hover:bg-gray-50"
        >
          {t('common.prev')}
        </button>
        <span className="px-3 py-1 text-sm">
          {page} / {totalPages}
        </span>
        <button
          disabled={page >= totalPages}
          onClick={() => onChange(page + 1)}
          className="px-3 py-1 text-sm rounded border disabled:opacity-40 hover:bg-gray-50"
        >
          {t('common.next')}
        </button>
      </div>
    </div>
  );
}
