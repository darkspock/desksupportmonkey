import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { StatusBadge } from '../../components/ui/Badge';
import { Table, Th, Td } from '../../components/ui/Table';
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
    <div>
      <h2 className="text-xl font-bold text-gray-900 mb-4">{t('page.my_equipment.title')}</h2>
      <Card>
        {isLoading ? (
          <Loading />
        ) : isError ? (
          <ErrorState
            message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
            onRetry={() => {
              void refetch();
            }}
          />
        ) : !data?.length ? (
          <EmptyState
            message={t('page.my_equipment.empty')}
            action={(
              <Link
                to="/my/requests/new"
                className="inline-flex rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                {t('page.my_equipment.request_cta')}
              </Link>
            )}
          />
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>{t('table.type')}</Th>
                <Th>{t('table.brand')}</Th>
                <Th>{t('table.model')}</Th>
                <Th>{t('table.serial_number')}</Th>
                <Th>{t('table.status')}</Th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.map((a) => (
                <tr key={a.id}>
                  <Td>{t(`enum.${a.type}`)}</Td>
                  <Td>{a.brand}</Td>
                  <Td>{a.model}</Td>
                  <Td>{a.serial_number}</Td>
                  <Td><StatusBadge status={a.status} /></Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
    </div>
  );
}
