import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { StatusBadge } from '../../components/ui/Badge';
import { Card } from '../../components/ui/Card';
import { Table, Th, Td } from '../../components/ui/Table';
import type { Asset, AssetEvent } from '../../types';

export default function AssetDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data: asset, isLoading } = useQuery({
    queryKey: ['asset', id],
    queryFn: async () => {
      const { data } = await api.get(`/assets/${id}`);
      return data.data as Asset;
    },
  });

  const { data: events } = useQuery({
    queryKey: ['asset-events', id],
    queryFn: async () => {
      const { data } = await api.get(`/assets/${id}/history`);
      return data.data as AssetEvent[];
    },
  });

  if (isLoading) return <Loading />;
  if (!asset) return <p className="text-red-600">Asset not found</p>;

  return (
    <div className="max-w-3xl space-y-6">
      <Card>
        <h2 className="text-xl font-bold text-gray-900 mb-4">{asset.brand} {asset.model}</h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div><span className="text-gray-500">Serial:</span> {asset.serial_number}</div>
          <div><span className="text-gray-500">Type:</span> {asset.type}</div>
          <div><span className="text-gray-500">Status:</span> <StatusBadge status={asset.status} /></div>
          <div><span className="text-gray-500">Assigned to:</span> {asset.assigned_to || '-'}</div>
          <div><span className="text-gray-500">Purchase date:</span> {asset.purchase_date || '-'}</div>
          <div><span className="text-gray-500">Warranty:</span> {asset.warranty_expiration || '-'}</div>
        </div>
        {asset.notes && <p className="text-sm text-gray-600 mt-4 bg-gray-50 rounded p-3">{asset.notes}</p>}
      </Card>

      <Card>
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Event History</h3>
        {!events?.length ? (
          <p className="text-sm text-gray-400">No events recorded.</p>
        ) : (
          <Table>
            <thead><tr><Th>Event</Th><Th>By</Th><Th>Date</Th><Th>Details</Th></tr></thead>
            <tbody className="divide-y divide-gray-100">
              {events.map((e) => (
                <tr key={e.id}>
                  <Td>{e.event_type}</Td>
                  <Td>{e.performed_by}</Td>
                  <Td>{new Date(e.created_at).toLocaleString()}</Td>
                  <Td><pre className="text-xs">{JSON.stringify(e.data, null, 2)}</pre></Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
    </div>
  );
}
