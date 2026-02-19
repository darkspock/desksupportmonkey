import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { StatusBadge } from '../../components/ui/Badge';
import { Table, Th, Td, Tr } from '../../components/ui/Table';
import { Card } from '../../components/ui/Card';
import { useI18n } from '../../lib/i18n';
import type { Asset } from '../../types';

export default function MyEquipmentPage() {
  const { t } = useI18n();
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['my-equipment'],
    queryFn: async () => {
      const { data } = await api.get('/my/equipment');
      return data.data as Asset[];
    },
  });

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.my_equipment.title')}</h2>
        <p className="mt-1 text-sm text-muted-foreground">{t('page.my_equipment.subtitle')}</p>
      </div>

      {/* Table */}
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
          <div className="p-5">
            <EmptyState
              message={t('page.my_equipment.empty')}
              action={(
                <Link
                  to="/my/requests/new"
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                >
                  {t('page.my_equipment.request_cta')}
                </Link>
              )}
            />
          </div>
        ) : (
          <Table>
            <thead>
              <tr className="hover:bg-transparent">
                <Th className="pl-4">{t('table.type')}</Th>
                <Th>{t('table.brand')}</Th>
                <Th>{t('table.model')}</Th>
                <Th>{t('table.serial_number')}</Th>
                <Th>{t('table.status')}</Th>
              </tr>
            </thead>
            <tbody>
              {data.map((a) => (
                <Tr key={a.id}>
                  <Td className="pl-4">{t(`enum.${a.type}`)}</Td>
                  <Td>{a.brand}</Td>
                  <Td>{a.model}</Td>
                  <Td><span className="font-mono text-xs">{a.serial_number}</span></Td>
                  <Td><StatusBadge status={a.status} /></Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
    </div>
  );
}
