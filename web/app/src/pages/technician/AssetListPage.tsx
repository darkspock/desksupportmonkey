import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { StatusBadge } from '../../components/ui/Badge';
import { Table, Th, Td, Tr } from '../../components/ui/Table';
import { Pagination } from '../../components/ui/Pagination';
import { Tooltip } from '../../components/ui/Tooltip';
import { EmployeeSearchSelect } from '../../components/ui/EmployeeSearchSelect';
import { useI18n } from '../../lib/i18n';
import type { Asset, AssetLocation, AssignableUser, PaginatedResponse } from '../../types';

export default function AssetListPage() {
  const { t } = useI18n();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [type, setType] = useState('');
  const [status, setStatus] = useState('');
  const [assignedTo, setAssignedTo] = useState('');
  const [locationId, setLocationId] = useState('');

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['assets', page, search, type, status, assignedTo, locationId],
    queryFn: async () => {
      const params: Record<string, unknown> = { page, page_size: 20 };
      if (search) params.search = search;
      if (type) params.type = type;
      if (status) params.status = status;
      if (assignedTo) params.assigned_to = assignedTo;
      if (locationId) params.location_id = locationId;
      const { data } = await api.get('/assets', { params });
      return data as PaginatedResponse<Asset>;
    },
  });

  const { data: locations } = useQuery({
    queryKey: ['locations-filter'],
    queryFn: async () => {
      const { data } = await api.get('/assets/locations');
      return data.data as AssetLocation[];
    },
  });

  const { data: assignableUsers } = useQuery({
    queryKey: ['assets-assignable-users-filter'],
    queryFn: async () => {
      const { data } = await api.get('/assets/assignable-users');
      return data.data as AssignableUser[];
    },
  });

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.asset_list.title')}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{t('page.asset_list.subtitle')}</p>
        </div>
        <div className="flex gap-2">
          <Link
            to="/assets/import"
            className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all"
          >
            {t('page.asset_list.import_csv')}
          </Link>
          <Link
            to="/assets/new"
            className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90"
          >
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5v14" /></svg>
            {t('page.asset_list.new_asset')}
          </Link>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <svg
            className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground pointer-events-none"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            viewBox="0 0 24 24"
          >
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.3-4.3" />
          </svg>
          <input
            type="search"
            placeholder={t('page.asset_list.search_placeholder')}
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="w-full pl-9 bg-card"
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          <select
            value={type}
            onChange={(e) => { setType(e.target.value); setPage(1); }}
            className="w-[150px] bg-card"
          >
            <option value="">{t('page.asset_list.all_types')}</option>
            {['laptop', 'desktop', 'phone', 'tablet', 'monitor', 'printer', 'other'].map((assetType) => (
              <option key={assetType} value={assetType}>{t(`enum.${assetType}`)}</option>
            ))}
          </select>
          <select
            value={status}
            onChange={(e) => { setStatus(e.target.value); setPage(1); }}
            className="w-[150px] bg-card"
          >
            <option value="">{t('page.asset_list.all_statuses')}</option>
            {['in_stock', 'assigned', 'in_repair', 'decommissioned'].map((s) => (
              <option key={s} value={s}>{t(`enum.${s}`)}</option>
            ))}
          </select>
          <EmployeeSearchSelect
            users={assignableUsers ?? []}
            value={assignedTo}
            onChange={(next) => { setAssignedTo(next); setPage(1); }}
            placeholder={t('page.asset_list.search_assignee')}
            allLabel={t('page.asset_list.all_assignees')}
            noResultsLabel={t('page.asset_list.no_assignee_results')}
          />
          <select
            value={locationId}
            onChange={(e) => { setLocationId(e.target.value); setPage(1); }}
            className="w-[180px] bg-card"
          >
            <option value="">{t('page.asset_list.all_locations')}</option>
            {(locations ?? []).map((loc) => (
              <option key={loc.id} value={loc.id}>{loc.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      {isLoading ? <Loading /> : isError ? (
        <ErrorState
          message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
          onRetry={() => { void refetch(); }}
        />
      ) : !data?.data.length ? (
        <EmptyState message={t('page.asset_list.empty')} />
      ) : (
        <>
          <Table>
            <thead>
              <tr className="hover:bg-transparent">
                <Th className="pl-4">{t('table.brand')}</Th>
                <Th className="hidden sm:table-cell">{t('table.serial')}</Th>
                <Th>{t('table.type')}</Th>
                <Th>{t('table.status')}</Th>
                <Th className="hidden lg:table-cell">{t('table.location')}</Th>
                <Th className="hidden lg:table-cell">{t('table.assigned')}</Th>
                <Th className="w-[88px] pr-4">
                  <span className="sr-only">{t('table.actions')}</span>
                </Th>
              </tr>
            </thead>
            <tbody>
              {data.data.map((a) => (
                <Tr key={a.id}>
                  <Td className="pl-4">
                    <Link to={`/assets/${a.id}`} className="text-sm font-medium text-foreground hover:text-primary transition-colors">
                      {a.brand}
                    </Link>
                    <p className="text-xs text-muted-foreground">{a.model}</p>
                  </Td>
                  <Td className="hidden sm:table-cell"><span className="text-sm font-mono text-muted-foreground">{a.serial_number}</span></Td>
                  <Td><span className="text-sm text-muted-foreground">{t(`enum.${a.type}`)}</span></Td>
                  <Td><StatusBadge status={a.status} /></Td>
                  <Td className="hidden lg:table-cell">
                    <span className="text-sm text-muted-foreground">{a.location_name || '—'}</span>
                  </Td>
                  <Td className="hidden lg:table-cell">
                    <span className="text-sm text-muted-foreground">{a.assigned_to_email || a.assigned_to || '—'}</span>
                  </Td>
                  <td className="px-3 py-3 text-sm">
                    <div className="flex items-center justify-end gap-1.5">
                      <Tooltip content={t('table.details')}>
                        <Link
                          to={`/assets/${a.id}`}
                          aria-label={t('table.details')}
                          className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-input text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
                        >
                          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
                            <circle cx="12" cy="12" r="3" />
                          </svg>
                        </Link>
                      </Tooltip>
                      <Tooltip content={t('page.asset_list.create_maintenance')}>
                        <Link
                          to={`/maintenance/new?asset_id=${encodeURIComponent(a.id)}`}
                          aria-label={t('page.asset_list.create_maintenance')}
                          className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-input text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
                        >
                          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76Z" />
                          </svg>
                        </Link>
                      </Tooltip>
                    </div>
                  </td>
                </Tr>
              ))}
            </tbody>
          </Table>
          <Pagination page={page} pageSize={20} total={data.meta.total} onChange={setPage} />
        </>
      )}
    </div>
  );
}
