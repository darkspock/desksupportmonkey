import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { StatusBadge } from '../../components/ui/Badge';
import { Table, Th, Td } from '../../components/ui/Table';
import { Card } from '../../components/ui/Card';
import type { Asset } from '../../types';

export default function MyEquipmentPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['my-equipment'],
    queryFn: async () => {
      const { data } = await api.get('/my/equipment');
      return data.data as Asset[];
    },
  });

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-900 mb-4">My Equipment</h2>
      <Card>
        {isLoading ? (
          <Loading />
        ) : !data?.length ? (
          <p className="text-sm text-gray-500">No equipment assigned to you.</p>
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Type</Th>
                <Th>Brand</Th>
                <Th>Model</Th>
                <Th>Serial Number</Th>
                <Th>Status</Th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.map((a) => (
                <tr key={a.id}>
                  <Td>{a.type.replace('_', ' ')}</Td>
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
