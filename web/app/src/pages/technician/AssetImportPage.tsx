import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Card } from '../../components/ui/Card';

export default function AssetImportPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<{ created: number; errors: string[] } | null>(null);

  const mutation = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error('No file selected');
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await api.post('/assets/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return data.data;
    },
    onSuccess: (data) => {
      setResult(data);
      queryClient.invalidateQueries({ queryKey: ['assets'] });
    },
  });

  return (
    <div className="max-w-xl">
      <h2 className="text-xl font-bold text-gray-900 mb-4">Import Assets from CSV</h2>
      <Card>
        <p className="text-sm text-gray-500 mb-4">
          CSV must include columns: type, brand, model, serial_number. Optional: purchase_date, warranty_expiration, notes.
        </p>

        {result ? (
          <div>
            <p className="text-sm text-green-600 mb-2">{result.created} assets imported successfully.</p>
            {result.errors?.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded p-3 mb-4">
                <p className="text-sm text-red-600 font-medium mb-1">{result.errors.length} error(s):</p>
                <ul className="text-xs text-red-500 list-disc pl-4">
                  {result.errors.map((e, i) => <li key={i}>{e}</li>)}
                </ul>
              </div>
            )}
            <button onClick={() => navigate('/assets')} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm">
              Back to Assets
            </button>
          </div>
        ) : (
          <form onSubmit={(e) => { e.preventDefault(); mutation.mutate(); }} className="space-y-4">
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            <div className="flex gap-3">
              <button type="submit" disabled={!file || mutation.isPending} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm disabled:opacity-50">
                {mutation.isPending ? 'Importing...' : 'Import'}
              </button>
              <button type="button" onClick={() => navigate(-1)} className="px-4 py-2 rounded-lg text-sm border hover:bg-gray-50">Cancel</button>
            </div>
          </form>
        )}
      </Card>
    </div>
  );
}
