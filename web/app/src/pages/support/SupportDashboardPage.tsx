import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import { useI18n } from '../../lib/i18n';
import { useSupportTickets, useSupportTicketStats } from '../../hooks/useSupportAdmin';
import { TicketStatusBadge } from '../../components/support/TicketStatusBadge';
import { useDebounce } from '../../hooks/useDebounce';

const CATEGORIES = ['bug_report', 'feature_request', 'billing', 'how_to', 'account_access', 'other'];
const STATUSES = ['open', 'in_progress', 'waiting_on_customer', 'resolved', 'closed'];
const PRIORITIES = ['low', 'medium', 'high', 'urgent'];

export default function SupportDashboardPage() {
  const { t } = useI18n();
  const navigate = useNavigate();

  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [sortBy, setSortBy] = useState<string>('created_at');
  const [sortOrder, setSortOrder] = useState<string>('desc');

  const debouncedSearch = useDebounce(searchInput, 300);

  const { data: statsData } = useSupportTicketStats();
  const stats = statsData?.data;

  const { data, isLoading } = useSupportTickets({
    page,
    status: statusFilter || undefined,
    priority: priorityFilter || undefined,
    category: categoryFilter || undefined,
    search: debouncedSearch || undefined,
    sort_by: sortBy,
    sort_order: sortOrder,
  });

  const tickets = data?.data ?? [];
  const meta = data?.meta;
  const totalPages = meta ? Math.ceil(meta.total / meta.page_size) : 1;

  const handleSort = (col: string) => {
    if (sortBy === col) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(col);
      setSortOrder('desc');
    }
    setPage(1);
  };

  const handleStatCardClick = (status: string) => {
    setStatusFilter(prev => prev === status ? '' : status);
    setPage(1);
  };

  const handleFilterChange = (setter: (v: string) => void) => (e: React.ChangeEvent<HTMLSelectElement>) => {
    setter(e.target.value);
    setPage(1);
  };

  const SortIcon = ({ col }: { col: string }) => {
    if (sortBy !== col) return <ArrowUpDown className="h-3 w-3 ml-1 opacity-30" />;
    return sortOrder === 'asc'
      ? <ArrowUp className="h-3 w-3 ml-1" />
      : <ArrowDown className="h-3 w-3 ml-1" />;
  };

  const statCards = useMemo(() => [
    { key: 'open', label: t('support_dashboard.stat_open'), count: stats?.open ?? 0, color: 'bg-blue-50 text-blue-700 border-blue-200' },
    { key: 'in_progress', label: t('support_dashboard.stat_in_progress'), count: stats?.in_progress ?? 0, color: 'bg-yellow-50 text-yellow-700 border-yellow-200' },
    { key: 'waiting_on_customer', label: t('support_dashboard.stat_waiting'), count: stats?.waiting_on_customer ?? 0, color: 'bg-orange-50 text-orange-700 border-orange-200' },
    { key: 'resolved', label: t('support_dashboard.stat_resolved'), count: stats?.resolved ?? 0, color: 'bg-green-50 text-green-700 border-green-200' },
  ], [stats, t]);

  const columns = [
    { key: 'reference', label: t('support_dashboard.col_reference'), sortable: true },
    { key: 'company_id', label: t('support_dashboard.col_company'), sortable: false },
    { key: 'created_by_email', label: t('support_dashboard.col_creator'), sortable: false },
    { key: 'subject', label: t('support_dashboard.col_subject'), sortable: true },
    { key: 'category', label: t('support_dashboard.col_category'), sortable: true },
    { key: 'status', label: t('support_dashboard.col_status'), sortable: true },
    { key: 'priority', label: t('support_dashboard.col_priority'), sortable: true },
    { key: 'created_at', label: t('support_dashboard.col_created'), sortable: true },
    { key: 'updated_at', label: t('support_dashboard.col_updated'), sortable: true },
  ];

  const formatDate = (d: string | null) => d ? new Date(d).toLocaleDateString() : '—';

  const formatCategory = (cat: string) => t(`support_ticket.category_${cat}` as any) || cat;

  const formatPriority = (p: string) => {
    const colors: Record<string, string> = {
      low: 'text-slate-600',
      medium: 'text-blue-600',
      high: 'text-orange-600',
      urgent: 'text-red-600 font-semibold',
    };
    return <span className={colors[p] || ''}>{p.charAt(0).toUpperCase() + p.slice(1)}</span>;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">{t('support_dashboard.title')}</h1>
        <p className="text-sm text-muted-foreground mt-1">{t('support_dashboard.subtitle')}</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
        {statCards.map(card => (
          <button
            key={card.key}
            type="button"
            onClick={() => handleStatCardClick(card.key)}
            className={`rounded-lg border p-4 text-center transition-all hover:shadow-md ${card.color} ${statusFilter === card.key ? 'ring-2 ring-primary ring-offset-1' : ''}`}
          >
            <div className="text-2xl font-bold">{card.count}</div>
            <div className="text-xs mt-1">{card.label}</div>
          </button>
        ))}
        <div className="rounded-lg border p-4 text-center bg-amber-50 text-amber-700 border-amber-200">
          <div className="text-2xl font-bold">
            {stats?.avg_satisfaction_rating != null
              ? `${stats.avg_satisfaction_rating.toFixed(1)} / 5`
              : '—'}
          </div>
          <div className="text-xs mt-1">{t('support_dashboard.stat_satisfaction')}</div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <select
          value={statusFilter}
          onChange={handleFilterChange(setStatusFilter)}
          className="rounded-md border border-input bg-background px-3 py-2 text-sm"
        >
          <option value="">{t('support_dashboard.filter_status')}: {t('support_dashboard.filter_all')}</option>
          {STATUSES.map(s => (
            <option key={s} value={s}>{t(`support_ticket.status_${s}` as any)}</option>
          ))}
        </select>

        <select
          value={priorityFilter}
          onChange={handleFilterChange(setPriorityFilter)}
          className="rounded-md border border-input bg-background px-3 py-2 text-sm"
        >
          <option value="">{t('support_dashboard.filter_priority')}: {t('support_dashboard.filter_all')}</option>
          {PRIORITIES.map(p => (
            <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
          ))}
        </select>

        <select
          value={categoryFilter}
          onChange={handleFilterChange(setCategoryFilter)}
          className="rounded-md border border-input bg-background px-3 py-2 text-sm"
        >
          <option value="">{t('support_dashboard.filter_category')}: {t('support_dashboard.filter_all')}</option>
          {CATEGORIES.map(c => (
            <option key={c} value={c}>{formatCategory(c)}</option>
          ))}
        </select>

        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            value={searchInput}
            onChange={e => { setSearchInput(e.target.value); setPage(1); }}
            placeholder={t('support_dashboard.search_placeholder')}
            className="w-full rounded-md border border-input bg-background pl-9 pr-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
      </div>

      {/* Table */}
      <div className="rounded-lg border border-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                {columns.map(col => (
                  <th
                    key={col.key}
                    className={`px-4 py-3 text-left font-medium text-muted-foreground ${col.sortable ? 'cursor-pointer select-none hover:text-foreground' : ''}`}
                    onClick={() => col.sortable && handleSort(col.key)}
                  >
                    <div className="flex items-center">
                      {col.label}
                      {col.sortable && <SortIcon col={col.key} />}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr><td colSpan={columns.length} className="px-4 py-8 text-center text-muted-foreground">Loading...</td></tr>
              ) : tickets.length === 0 ? (
                <tr><td colSpan={columns.length} className="px-4 py-8 text-center text-muted-foreground">{t('support_dashboard.empty')}</td></tr>
              ) : (
                tickets.map(ticket => (
                  <tr
                    key={ticket.id}
                    onClick={() => navigate(`/platform/support-tickets/${ticket.id}`)}
                    className="border-b border-border hover:bg-muted/30 cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-3 font-mono text-xs">{ticket.reference}</td>
                    <td className="px-4 py-3 truncate max-w-[120px]">{ticket.company_id ?? '—'}</td>
                    <td className="px-4 py-3 truncate max-w-[160px]">{ticket.created_by_email ?? '—'}</td>
                    <td className="px-4 py-3 truncate max-w-[200px]">{ticket.subject}</td>
                    <td className="px-4 py-3 text-xs">{formatCategory(ticket.category)}</td>
                    <td className="px-4 py-3"><TicketStatusBadge status={ticket.status} /></td>
                    <td className="px-4 py-3 text-xs">{formatPriority(ticket.priority)}</td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">{formatDate(ticket.created_at)}</td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">{formatDate(ticket.updated_at)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            type="button"
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="rounded-md border border-input px-3 py-1.5 text-sm disabled:opacity-50"
          >
            &lsaquo;
          </button>
          <span className="text-sm text-muted-foreground">
            {page} / {totalPages}
          </span>
          <button
            type="button"
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            className="rounded-md border border-input px-3 py-1.5 text-sm disabled:opacity-50"
          >
            &rsaquo;
          </button>
        </div>
      )}
    </div>
  );
}
