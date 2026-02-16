import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { StatusBadge } from '../../components/ui/Badge';
import { Table, Th, Td } from '../../components/ui/Table';
import { Card } from '../../components/ui/Card';
import type { Report, PaginatedResponse } from '../../types';

export default function ReportsPage() {
  const queryClient = useQueryClient();
  const [reportType, setReportType] = useState('asset_inventory');

  const { data, isLoading } = useQuery({
    queryKey: ['reports'],
    queryFn: async () => {
      const { data } = await api.get('/reports', { params: { page_size: 50 } });
      return data as PaginatedResponse<Report>;
    },
    refetchInterval: 5000,
  });

  const create = useMutation({
    mutationFn: () => api.post('/reports', { type: reportType }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['reports'] }),
  });

  const download = async (id: string) => {
    try {
      const { data } = await api.get(`/reports/${id}/download`);
      window.open(data.data.download_url, '_blank');
    } catch {
      alert('Download not available yet');
    }
  };

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-900 mb-4">Reports</h2>

      <Card className="mb-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Generate New Report</h3>
        <div className="flex gap-3 items-end">
          <div>
            <label className="block text-sm text-gray-600 mb-1">Type</label>
            <select value={reportType} onChange={(e) => setReportType(e.target.value)} className="border rounded-lg px-3 py-2 text-sm">
              <option value="asset_inventory">Asset Inventory</option>
              <option value="request_summary">Request Summary</option>
              <option value="technician_performance">Technician Performance</option>
            </select>
          </div>
          <button onClick={() => create.mutate()} disabled={create.isPending} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
            {create.isPending ? 'Requesting...' : 'Generate'}
          </button>
        </div>
      </Card>

      <Card>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Report History</h3>
        {isLoading ? <Loading /> : !data?.data.length ? (
          <p className="text-sm text-gray-500">No reports generated yet.</p>
        ) : (
          <Table>
            <thead><tr><Th>Type</Th><Th>Status</Th><Th>Requested</Th><Th>Completed</Th><Th>Actions</Th></tr></thead>
            <tbody className="divide-y divide-gray-100">
              {data.data.map((r) => (
                <tr key={r.id}>
                  <Td>{r.type.replace('_', ' ')}</Td>
                  <Td><StatusBadge status={r.status} /></Td>
                  <Td>{new Date(r.created_at).toLocaleString()}</Td>
                  <Td>{r.completed_at ? new Date(r.completed_at).toLocaleString() : '-'}</Td>
                  <Td>
                    {r.status === 'completed' && (
                      <button onClick={() => download(r.id)} className="text-xs text-blue-600 hover:underline">Download</button>
                    )}
                    {r.status === 'failed' && (
                      <span className="text-xs text-red-500">{r.error_message || 'Failed'}</span>
                    )}
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
    </div>
  );
}
