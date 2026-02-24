import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { StatusBadge } from '../../components/ui/Badge';
import { Table, Th, Td, Tr } from '../../components/ui/Table';
import { Card } from '../../components/ui/Card';
import { formatDate } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import type { MyIncident } from '../../types';

export default function MyIncidentsPage() {
  const { t } = useI18n();

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['my-incidents'],
    queryFn: async () => {
      const { data } = await api.get('/my/incidents');
      return data as MyIncident[];
    },
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.my_incidents.title')}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{t('page.my_incidents.subtitle')}</p>
        </div>
        <Link
          to="/my/report-incident"
          className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
        >
          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M5 12h14M12 5v14" />
          </svg>
          {t('page.my_incidents.report_new')}
        </Link>
      </div>

      <Card className="overflow-hidden p-0">
        {isLoading ? (
          <div className="p-5"><Loading /></div>
        ) : isError ? (
          <div className="p-5">
            <ErrorState
              message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
              onRetry={() => { void refetch(); }}
            />
          </div>
        ) : !data?.length ? (
          <div className="p-5"><EmptyState message={t('page.my_incidents.empty')} /></div>
        ) : (
          <Table>
            <thead>
              <tr className="hover:bg-transparent">
                <Th className="pl-4">{t('table.title')}</Th>
                <Th>{t('table.type')}</Th>
                <Th>{t('table.severity')}</Th>
                <Th>{t('table.status')}</Th>
                <Th>{t('table.created')}</Th>
              </tr>
            </thead>
            <tbody>
              {data.map((inc) => (
                <Tr key={inc.id}>
                  <Td className="pl-4">
                    <span className="text-foreground font-medium">{inc.title}</span>
                  </Td>
                  <Td>{t(`enum.incident_type.${inc.incident_type}`)}</Td>
                  <Td><StatusBadge status={inc.severity} /></Td>
                  <Td><StatusBadge status={inc.status} /></Td>
                  <Td>{formatDate(inc.created_at)}</Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
    </div>
  );
}
