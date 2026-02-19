import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '../../lib/api';
import { Card } from '../../components/ui/Card';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../lib/i18n';
import type { ShippingAddress, Asset, PaginatedResponse } from '../../types';

export default function ShipmentCreatePage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const returnFor = searchParams.get('return_for');
  const requestId = searchParams.get('request_id');
  const { showToast } = useToast();
  const { t } = useI18n();

  const [direction, setDirection] = useState<'outbound' | 'inbound'>(returnFor ? 'inbound' : 'outbound');
  const [destType, setDestType] = useState<'employee_home' | 'office' | 'vendor'>('employee_home');
  const [originAddrId, setOriginAddrId] = useState('');
  const [destAddrId, setDestAddrId] = useState('');
  const [carrier, setCarrier] = useState('');
  const [trackingNumber, setTrackingNumber] = useState('');
  const [trackingUrl, setTrackingUrl] = useState('');
  const [recipientName, setRecipientName] = useState('');
  const [notes, setNotes] = useState('');
  const [selectedAssets, setSelectedAssets] = useState<string[]>([]);
  const [assetSearch, setAssetSearch] = useState('');
  const [formError, setFormError] = useState('');

  const addressesQuery = useQuery({
    queryKey: ['addresses-all'],
    queryFn: async () => {
      const { data } = await api.get('/addresses', { params: { page_size: 100, is_active: true } });
      return data as PaginatedResponse<ShippingAddress>;
    },
  });

  const assetsQuery = useQuery({
    queryKey: ['assets-for-shipment'],
    queryFn: async () => {
      const { data } = await api.get('/assets', { params: { page_size: 100 } });
      return data as PaginatedResponse<Asset>;
    },
  });

  const createShipment = useMutation({
    mutationFn: async () => {
      const payload: Record<string, unknown> = {
        direction,
        destination_type: destType,
        asset_ids: selectedAssets,
      };
      if (originAddrId) payload.origin_address_id = originAddrId;
      if (destAddrId) payload.destination_address_id = destAddrId;
      if (carrier) payload.carrier = carrier;
      if (trackingNumber) payload.tracking_number = trackingNumber;
      if (trackingUrl) payload.tracking_url = trackingUrl;
      if (recipientName) payload.recipient_name = recipientName;
      if (notes) payload.notes = notes;
      if (requestId) payload.request_id = requestId;
      if (returnFor) payload.return_for_shipment_id = returnFor;
      const { data } = await api.post('/shipments', payload);
      return data.data as { id: string };
    },
    onSuccess: (data) => {
      showToast({ title: t('page.shipment_create.toast_created'), variant: 'success' });
      navigate(`/shipments/${data.id}`);
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.shipment_create.error_create');
      setFormError(detail);
      showToast({ title: t('page.shipment_create.error_create'), description: detail, variant: 'error' });
    },
  });

  const addrList = addressesQuery.data?.data ?? [];
  const assetList = assetsQuery.data?.data ?? [];
  const filteredAssets = assetSearch
    ? assetList.filter((a) =>
        a.brand.toLowerCase().includes(assetSearch.toLowerCase()) ||
        a.model.toLowerCase().includes(assetSearch.toLowerCase()) ||
        a.serial_number.toLowerCase().includes(assetSearch.toLowerCase())
      )
    : assetList;

  const toggleAsset = (assetId: string) => {
    if (formError) setFormError('');
    setSelectedAssets((prev) =>
      prev.includes(assetId) ? prev.filter((id) => id !== assetId) : [...prev, assetId],
    );
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setFormError('');
    if (!selectedAssets.length) {
      setFormError(t('page.shipment_create.error_assets_required'));
      return;
    }
    createShipment.mutate();
  };

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-5">
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.shipment_create.title')}</h2>
        <p className="mt-1 text-sm text-muted-foreground">{t('page.shipment_create.subtitle')}</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {formError && (
          <div className="rounded-md border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {formError}
          </div>
        )}

        <Card className="overflow-hidden p-0">
          <div className="border-b border-border px-5 py-3.5">
            <h3 className="text-sm font-medium text-foreground">{t('page.shipment_create.section_setup')}</h3>
          </div>

          <div className="space-y-4 p-5">
            {(requestId || returnFor) && (
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                {requestId && (
                  <div className="rounded-md border border-border bg-secondary/40 px-3 py-2 text-sm">
                    <span className="text-muted-foreground">{t('page.shipment_create.linked_request')}:</span>{' '}
                    <span className="font-mono text-xs text-foreground">{requestId}</span>
                  </div>
                )}
                {returnFor && (
                  <div className="rounded-md border border-border bg-secondary/40 px-3 py-2 text-sm">
                    <span className="text-muted-foreground">{t('page.shipment_create.return_for')}:</span>{' '}
                    <span className="font-mono text-xs text-foreground">{returnFor}</span>
                  </div>
                )}
              </div>
            )}

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <fieldset>
                <legend className="mb-1.5 block text-sm text-muted-foreground">{t('page.shipment_create.direction')}</legend>
                <div className="flex flex-wrap gap-2">
                  {(['outbound', 'inbound'] as const).map((d) => (
                    <button
                      key={d}
                      type="button"
                      onClick={() => setDirection(d)}
                      className={`inline-flex h-9 items-center justify-center rounded-md border px-3 text-sm font-medium transition-colors ${
                        direction === d
                          ? 'border-primary bg-primary text-primary-foreground'
                          : 'border-border bg-card text-foreground hover:bg-accent hover:text-accent-foreground'
                      }`}
                    >
                      {t(`enum.shipment_direction.${d}`)}
                    </button>
                  ))}
                </div>
              </fieldset>

              <fieldset>
                <legend className="mb-1.5 block text-sm text-muted-foreground">{t('page.shipment_create.destination_type')}</legend>
                <div className="flex flex-wrap gap-2">
                  {(['employee_home', 'office', 'vendor'] as const).map((d) => (
                    <button
                      key={d}
                      type="button"
                      onClick={() => setDestType(d)}
                      className={`inline-flex h-9 items-center justify-center rounded-md border px-3 text-sm font-medium transition-colors ${
                        destType === d
                          ? 'border-primary bg-primary text-primary-foreground'
                          : 'border-border bg-card text-foreground hover:bg-accent hover:text-accent-foreground'
                      }`}
                    >
                      {t(`enum.destination_type.${d}`)}
                    </button>
                  ))}
                </div>
              </fieldset>
            </div>
          </div>
        </Card>

        <Card className="overflow-hidden p-0">
          <div className="border-b border-border px-5 py-3.5">
            <h3 className="text-sm font-medium text-foreground">{t('page.shipment_create.section_shipping')}</h3>
          </div>

          <div className="space-y-4 p-5">
            {addressesQuery.isError && (
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                <span>{t('page.shipment_create.error_addresses_load')}</span>
                <button
                  type="button"
                  onClick={() => { void addressesQuery.refetch(); }}
                  className="inline-flex items-center justify-center rounded-md border border-destructive/30 bg-background px-3 py-1 text-xs font-medium text-foreground hover:bg-accent"
                >
                  {t('common.retry')}
                </button>
              </div>
            )}

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <label className="mb-1.5 block text-sm text-muted-foreground">{t('page.shipment_create.origin_address')}</label>
                <select
                  value={originAddrId}
                  onChange={(e) => setOriginAddrId(e.target.value)}
                  className="w-full bg-card"
                  disabled={addressesQuery.isLoading}
                >
                  <option value="">
                    {addressesQuery.isLoading ? t('page.shipment_create.loading_addresses') : t('page.shipment_create.select_address')}
                  </option>
                  {addrList.map((a) => (
                    <option key={a.id} value={a.id}>{a.label} — {a.city}, {a.state}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="mb-1.5 block text-sm text-muted-foreground">{t('page.shipment_create.destination_address')}</label>
                <select
                  value={destAddrId}
                  onChange={(e) => setDestAddrId(e.target.value)}
                  className="w-full bg-card"
                  disabled={addressesQuery.isLoading}
                >
                  <option value="">
                    {addressesQuery.isLoading ? t('page.shipment_create.loading_addresses') : t('page.shipment_create.select_address')}
                  </option>
                  {addrList.map((a) => (
                    <option key={a.id} value={a.id}>{a.label} — {a.city}, {a.state}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <div>
                <label className="mb-1.5 block text-sm text-muted-foreground">{t('page.shipment_create.carrier')}</label>
                <input value={carrier} onChange={(e) => setCarrier(e.target.value)} className="w-full bg-card" />
              </div>

              <div>
                <label className="mb-1.5 block text-sm text-muted-foreground">{t('page.shipment_create.tracking_number')}</label>
                <input value={trackingNumber} onChange={(e) => setTrackingNumber(e.target.value)} className="w-full bg-card" />
              </div>

              <div>
                <label className="mb-1.5 block text-sm text-muted-foreground">{t('page.shipment_create.tracking_url')}</label>
                <input value={trackingUrl} onChange={(e) => setTrackingUrl(e.target.value)} className="w-full bg-card" />
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <label className="mb-1.5 block text-sm text-muted-foreground">{t('page.shipment_create.recipient_name')}</label>
                <input value={recipientName} onChange={(e) => setRecipientName(e.target.value)} className="w-full bg-card" />
              </div>

              <div>
                <label className="mb-1.5 block text-sm text-muted-foreground">{t('page.shipment_create.notes')}</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                  className="w-full resize-none bg-card"
                />
              </div>
            </div>
          </div>
        </Card>

        <Card className="overflow-hidden p-0">
          <div className="border-b border-border px-5 py-3.5">
            <h3 className="text-sm font-medium text-foreground">
              {t('page.shipment_create.assets')}
              {selectedAssets.length > 0 && (
                <span className="ml-2 text-xs text-muted-foreground">
                  {t('page.shipment_create.selected_count', { count: selectedAssets.length })}
                </span>
              )}
            </h3>
          </div>

          <div className="space-y-3 p-5">
            {assetsQuery.isError && (
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                <span>{t('page.shipment_create.error_assets_load')}</span>
                <button
                  type="button"
                  onClick={() => { void assetsQuery.refetch(); }}
                  className="inline-flex items-center justify-center rounded-md border border-destructive/30 bg-background px-3 py-1 text-xs font-medium text-foreground hover:bg-accent"
                >
                  {t('common.retry')}
                </button>
              </div>
            )}

            <input
              value={assetSearch}
              onChange={(e) => setAssetSearch(e.target.value)}
              placeholder={t('page.shipment_create.search_assets')}
              className="w-full bg-card"
            />

            <div className="overflow-hidden rounded-lg border border-border">
              {assetsQuery.isLoading ? (
                <p className="p-3 text-sm text-muted-foreground">{t('page.shipment_create.loading_assets')}</p>
              ) : filteredAssets.length === 0 ? (
                <p className="p-3 text-sm text-muted-foreground">{t('page.shipment_create.no_assets')}</p>
              ) : (
                <div className="max-h-72 overflow-auto">
                  <table className="w-full min-w-[680px] text-sm">
                    <thead>
                      <tr className="bg-secondary/40">
                        <th className="w-10 px-3 py-2 text-left font-medium text-muted-foreground" />
                        <th className="px-3 py-2 text-left font-medium text-muted-foreground">{t('table.asset')}</th>
                        <th className="px-3 py-2 text-left font-medium text-muted-foreground">{t('table.serial')}</th>
                        <th className="px-3 py-2 text-left font-medium text-muted-foreground">{t('table.status')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredAssets.map((asset) => (
                        <tr key={asset.id} className="border-t border-border hover:bg-accent/30">
                          <td className="px-3 py-2">
                            <input
                              type="checkbox"
                              checked={selectedAssets.includes(asset.id)}
                              onChange={() => toggleAsset(asset.id)}
                              className="rounded"
                            />
                          </td>
                          <td className="px-3 py-2 text-foreground">{asset.brand} {asset.model}</td>
                          <td className="px-3 py-2 text-muted-foreground">{asset.serial_number}</td>
                          <td className="px-3 py-2 text-muted-foreground">
                            {t(`enum.${asset.status}`, undefined, { defaultValue: asset.status })}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </Card>

        <div className="flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={() => navigate('/shipments')}
            className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
          >
            {t('common.cancel')}
          </button>
          <button
            type="submit"
            disabled={createShipment.isPending}
            className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
          >
            {createShipment.isPending ? t('page.shipment_create.saving') : t('page.shipment_create.save_draft')}
          </button>
        </div>
      </form>
    </div>
  );
}
