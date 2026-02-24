import { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { ErrorState } from '../../components/ui/StateBlock';
import { Badge } from '../../components/ui/Badge';
import { Card } from '../../components/ui/Card';
import { Table, Th, Td } from '../../components/ui/Table';
import { useToast } from '../../hooks/useToast';
import { formatDateTime } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import type { Shipment, AssetLocation } from '../../types';

const statusColors: Record<string, string> = {
  DRAFT: 'default',
  DISPATCHED: 'info',
  IN_TRANSIT: 'warning',
  DELIVERED: 'success',
  FAILED: 'danger',
  CANCELLED: 'default',
};

function formatLocation(loc: AssetLocation | undefined): string {
  if (!loc) return '—';
  const parts: string[] = [loc.name];
  const addrParts = [loc.street_line_1, loc.city, loc.state, loc.postal_code].filter(Boolean);
  if (addrParts.length) parts.push(addrParts.join(', '));
  return parts.join(' — ');
}

export default function ShipmentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const { t } = useI18n();

  const [showDispatchForm, setShowDispatchForm] = useState(false);
  const [dispatchCarrier, setDispatchCarrier] = useState('');
  const [dispatchTracking, setDispatchTracking] = useState('');
  const [showFailDialog, setShowFailDialog] = useState(false);
  const [failReason, setFailReason] = useState('');
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const [cancelReason, setCancelReason] = useState('');

  // Inline edit state
  const [editing, setEditing] = useState(false);
  const [editCarrier, setEditCarrier] = useState('');
  const [editServiceLevel, setEditServiceLevel] = useState('');
  const [editTrackingNumber, setEditTrackingNumber] = useState('');
  const [editTrackingUrl, setEditTrackingUrl] = useState('');
  const [editItemsDescription, setEditItemsDescription] = useState('');
  const [editInternalNotes, setEditInternalNotes] = useState('');
  const [editNotes, setEditNotes] = useState('');

  const { data: shipment, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['shipment', id],
    queryFn: async () => {
      const { data } = await api.get(`/shipments/${id}`);
      return data.data as Shipment;
    },
    enabled: Boolean(id),
  });

  const { data: locations } = useQuery({
    queryKey: ['asset-locations'],
    queryFn: async () => {
      const { data } = await api.get('/assets/locations');
      return data.data as AssetLocation[];
    },
    enabled: Boolean(shipment),
  });

  const originLocation = locations?.find((l) => l.id === shipment?.origin_location_id);
  const destLocation = locations?.find((l) => l.id === shipment?.destination_location_id);

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['shipment', id] });
    queryClient.invalidateQueries({ queryKey: ['shipments'] });
  };

  const errDetail = (err: unknown) =>
    (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.shipment_detail.error_action');

  const startEditing = () => {
    if (!shipment) return;
    setEditCarrier(shipment.carrier ?? '');
    setEditServiceLevel(shipment.service_level ?? '');
    setEditTrackingNumber(shipment.tracking_number ?? '');
    setEditTrackingUrl(shipment.tracking_url ?? '');
    setEditItemsDescription(shipment.items_description ?? '');
    setEditInternalNotes(shipment.internal_notes ?? '');
    setEditNotes(shipment.notes ?? '');
    setEditing(true);
  };

  const updateShipment = useMutation({
    mutationFn: () => api.patch(`/shipments/${id}`, {
      carrier: editCarrier || null,
      service_level: editServiceLevel || null,
      tracking_number: editTrackingNumber || null,
      tracking_url: editTrackingUrl || null,
      items_description: editItemsDescription || null,
      internal_notes: editInternalNotes || null,
      notes: editNotes || null,
    }),
    onSuccess: () => {
      invalidate();
      setEditing(false);
      showToast({ title: t('page.shipment_detail.toast_updated'), variant: 'success' });
    },
    onError: (err: unknown) => showToast({ title: errDetail(err), variant: 'error', durationMs: 5000 }),
  });

  const dispatch = useMutation({
    mutationFn: () => api.post(`/shipments/${id}/dispatch`, {
      carrier: dispatchCarrier,
      tracking_number: dispatchTracking || null,
    }),
    onSuccess: () => {
      invalidate();
      setShowDispatchForm(false);
      showToast({ title: t('page.shipment_detail.toast_dispatched'), variant: 'success' });
    },
    onError: (err: unknown) => showToast({ title: errDetail(err), variant: 'error' }),
  });

  const markInTransit = useMutation({
    mutationFn: () => api.post(`/shipments/${id}/in-transit`),
    onSuccess: () => {
      invalidate();
      showToast({ title: t('page.shipment_detail.toast_in_transit'), variant: 'success' });
    },
    onError: (err: unknown) => showToast({ title: errDetail(err), variant: 'error' }),
  });

  const deliver = useMutation({
    mutationFn: () => api.post(`/shipments/${id}/deliver`),
    onSuccess: () => {
      invalidate();
      showToast({ title: t('page.shipment_detail.toast_delivered'), variant: 'success' });
    },
    onError: (err: unknown) => showToast({ title: errDetail(err), variant: 'error' }),
  });

  const fail = useMutation({
    mutationFn: () => api.post(`/shipments/${id}/fail`, { reason: failReason }),
    onSuccess: () => {
      invalidate();
      setShowFailDialog(false);
      setFailReason('');
      showToast({ title: t('page.shipment_detail.toast_failed'), variant: 'success' });
    },
    onError: (err: unknown) => showToast({ title: errDetail(err), variant: 'error' }),
  });

  const cancel = useMutation({
    mutationFn: () => api.post(`/shipments/${id}/cancel`, { reason: cancelReason }),
    onSuccess: () => {
      invalidate();
      setShowCancelDialog(false);
      setCancelReason('');
      showToast({ title: t('page.shipment_detail.toast_cancelled'), variant: 'success' });
    },
    onError: (err: unknown) => showToast({ title: errDetail(err), variant: 'error' }),
  });

  if (isLoading) return <Loading />;
  if (isError) {
    return (
      <ErrorState
        message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
        onRetry={() => { void refetch(); }}
      />
    );
  }
  if (!shipment) return <ErrorState message={t('page.shipment_detail.not_found')} />;

  const isDraft = shipment.status === 'draft';
  const isDispatched = shipment.status === 'dispatched';
  const isInTransit = shipment.status === 'in_transit';
  const isDelivered = shipment.status === 'delivered';
  const isTerminal = shipment.status === 'failed' || shipment.status === 'cancelled';

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <Card>
        <div className="flex items-start justify-between mb-4 gap-3">
          <div>
            <div className="flex gap-2 items-center flex-wrap">
              <Badge variant={statusColors[shipment.status] || 'default'}>
                {t(`enum.shipment_status.${shipment.status}`)}
              </Badge>
              <Badge variant={shipment.direction === 'outbound' ? 'info' : 'warning'}>
                {t(`enum.shipment_direction.${shipment.direction}`)}
              </Badge>
              <span className="text-xs text-muted-foreground">{t(`enum.destination_type.${shipment.destination_type}`)}</span>
            </div>
            <p className="mt-2 text-xs text-muted-foreground font-mono">{shipment.id}</p>
          </div>
          {!isTerminal && !editing && (
            <button
              onClick={startEditing}
              className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 h-8 text-xs font-medium text-foreground hover:bg-accent transition-all"
            >
              <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125" /></svg>
              {t('common.edit')}
            </button>
          )}
        </div>

        {editing ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-sm font-medium text-muted-foreground">{t('page.shipment_detail.carrier')}</label>
                <input value={editCarrier} onChange={(e) => setEditCarrier(e.target.value)} className="w-full" placeholder="FedEx, UPS, DHL..." />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-muted-foreground">{t('page.shipment_detail.service_level')}</label>
                <input value={editServiceLevel} onChange={(e) => setEditServiceLevel(e.target.value)} className="w-full" placeholder="Standard, 24h, 48h..." />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-muted-foreground">{t('page.shipment_detail.tracking')} #</label>
                <input value={editTrackingNumber} onChange={(e) => setEditTrackingNumber(e.target.value)} className="w-full" />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-muted-foreground">{t('page.shipment_detail.tracking')} URL</label>
                <input value={editTrackingUrl} onChange={(e) => setEditTrackingUrl(e.target.value)} className="w-full" placeholder="https://..." />
              </div>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-muted-foreground">{t('page.shipment_detail.items_description')}</label>
              <textarea value={editItemsDescription} onChange={(e) => setEditItemsDescription(e.target.value)} rows={3} className="w-full resize-none" />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-muted-foreground">{t('page.shipment_detail.internal_notes')}</label>
              <textarea value={editInternalNotes} onChange={(e) => setEditInternalNotes(e.target.value)} rows={2} className="w-full resize-none" />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-muted-foreground">{t('page.shipment_detail.notes')}</label>
              <textarea value={editNotes} onChange={(e) => setEditNotes(e.target.value)} rows={2} className="w-full resize-none" />
            </div>
            <div className="flex gap-2 pt-1">
              <button
                onClick={() => updateShipment.mutate()}
                disabled={updateShipment.isPending}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
              >
                {updateShipment.isPending ? t('common.saving') : t('common.save')}
              </button>
              <button
                onClick={() => setEditing(false)}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all"
              >
                {t('common.cancel')}
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div><span className="text-muted-foreground">{t('page.shipment_detail.carrier')}:</span> {shipment.carrier || '—'}</div>
            <div>
              <span className="text-muted-foreground">{t('page.shipment_detail.tracking')}:</span>{' '}
              {shipment.tracking_url ? (
                <a href={shipment.tracking_url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                  {shipment.tracking_number || t('page.shipment_detail.tracking')}
                </a>
              ) : (
                shipment.tracking_number || '—'
              )}
            </div>
            <div><span className="text-muted-foreground">{t('table.recipient')}:</span> {shipment.recipient_name || '—'}</div>
            <div><span className="text-muted-foreground">{t('table.items')}:</span> {shipment.item_count}</div>
            {shipment.service_level && (
              <div><span className="text-muted-foreground">{t('page.shipment_detail.service_level')}:</span> {shipment.service_level}</div>
            )}
            {shipment.items_description && (
              <div className="col-span-2"><span className="text-muted-foreground">{t('page.shipment_detail.items_description')}:</span> {shipment.items_description}</div>
            )}
            {shipment.internal_notes && (
              <div className="col-span-2"><span className="text-muted-foreground">{t('page.shipment_detail.internal_notes')}:</span> {shipment.internal_notes}</div>
            )}
            {shipment.dispatched_at && (
              <div><span className="text-muted-foreground">{t('page.shipment_detail.dispatched_at')}:</span> {formatDateTime(shipment.dispatched_at)}</div>
            )}
            {shipment.delivered_at && (
              <div><span className="text-muted-foreground">{t('page.shipment_detail.delivered_at')}:</span> {formatDateTime(shipment.delivered_at)}</div>
            )}
          </div>
        )}
      </Card>

      <Card>
        <h3 className="text-sm font-semibold text-foreground mb-3">{t('page.shipment_detail.addresses')}</h3>
        <div className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
          <div>
            <p className="text-xs text-muted-foreground mb-1">{t('page.shipment_detail.origin')}</p>
            <p className="text-foreground">{formatLocation(originLocation)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground mb-1">{t('page.shipment_detail.destination')}</p>
            <p className="text-foreground">{formatLocation(destLocation)}</p>
          </div>
        </div>
      </Card>

      {(shipment.request_id || shipment.po_id || shipment.return_for_shipment_id) && (
        <Card>
          <h3 className="text-sm font-semibold text-foreground mb-3">{t('page.shipment_detail.linked_records')}</h3>
          <div className="space-y-1 text-sm">
            {shipment.request_id && (
              <div>
                <span className="text-muted-foreground">{t('page.shipment_detail.request')}:</span>{' '}
                <Link to={`/requests/${shipment.request_id}`} className="text-primary hover:underline font-mono text-xs">{shipment.request_id.slice(0, 8)}</Link>
              </div>
            )}
            {shipment.po_id && (
              <div>
                <span className="text-muted-foreground">{t('page.shipment_detail.purchase_order')}:</span>{' '}
                <Link to={`/purchase-orders/${shipment.po_id}`} className="text-primary hover:underline font-mono text-xs">{shipment.po_id.slice(0, 8)}</Link>
              </div>
            )}
            {shipment.return_for_shipment_id && (
              <div>
                <span className="text-muted-foreground">{t('page.shipment_detail.return_for')}:</span>{' '}
                <Link to={`/shipments/${shipment.return_for_shipment_id}`} className="text-primary hover:underline font-mono text-xs">{shipment.return_for_shipment_id.slice(0, 8)}</Link>
              </div>
            )}
          </div>
        </Card>
      )}

      {(shipment.notes || shipment.failure_reason || shipment.cancellation_reason) && (
        <Card>
          <h3 className="text-sm font-semibold text-foreground mb-3">{t('page.shipment_detail.notes')}</h3>
          {shipment.notes && <p className="text-sm text-foreground mb-2">{shipment.notes}</p>}
          {shipment.failure_reason && (
            <p className="text-sm text-destructive"><span className="font-medium">{t('page.shipment_detail.failure_reason')}:</span> {shipment.failure_reason}</p>
          )}
          {shipment.cancellation_reason && (
            <p className="text-sm text-muted-foreground"><span className="font-medium">{t('page.shipment_detail.cancellation_reason')}:</span> {shipment.cancellation_reason}</p>
          )}
        </Card>
      )}

      <Card>
        <h3 className="text-sm font-semibold text-foreground mb-3">{t('page.shipment_detail.items')}</h3>
        {!shipment.items?.length ? (
          <p className="text-sm text-muted-foreground">{t('page.shipment_detail.no_items')}</p>
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>{t('table.asset')}</Th>
                <Th>{t('table.notes')}</Th>
              </tr>
            </thead>
            <tbody>
              {shipment.items.map((item) => (
                <tr key={item.id}>
                  <Td>
                    <Link to={`/assets/${item.asset_id}`} className="text-primary hover:underline font-mono text-xs">
                      {item.asset_id.slice(0, 8)}
                    </Link>
                  </Td>
                  <Td>{item.notes || '—'}</Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>

      {!isTerminal && (
        <Card>
          <div className="flex flex-wrap gap-2">
            {isDraft && (
              <>
                <button
                  onClick={() => setShowDispatchForm(!showDispatchForm)}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                >
                  {t('page.shipment_detail.dispatch')}
                </button>
                <button
                  onClick={() => setShowCancelDialog(true)}
                  className="rounded-md h-9 px-4 text-sm font-medium bg-destructive text-white shadow-xs hover:bg-destructive/90 disabled:opacity-50"
                >
                  {t('page.shipment_detail.cancel')}
                </button>
              </>
            )}
            {isDispatched && (
              <>
                <button onClick={() => markInTransit.mutate()} disabled={markInTransit.isPending} className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50 disabled:opacity-50">
                  {t('page.shipment_detail.mark_in_transit')}
                </button>
                <button onClick={() => deliver.mutate()} disabled={deliver.isPending} className="rounded-md h-9 px-4 text-sm font-medium bg-success text-white shadow-xs hover:bg-success/90 disabled:opacity-50">
                  {t('page.shipment_detail.deliver')}
                </button>
                <button onClick={() => setShowFailDialog(true)} className="rounded-md h-9 px-4 text-sm font-medium bg-destructive text-white shadow-xs hover:bg-destructive/90 disabled:opacity-50">
                  {t('page.shipment_detail.fail')}
                </button>
                <button onClick={() => setShowCancelDialog(true)} className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50">
                  {t('page.shipment_detail.cancel')}
                </button>
              </>
            )}
            {isInTransit && (
              <>
                <button onClick={() => deliver.mutate()} disabled={deliver.isPending} className="rounded-md h-9 px-4 text-sm font-medium bg-success text-white shadow-xs hover:bg-success/90 disabled:opacity-50">
                  {t('page.shipment_detail.deliver')}
                </button>
                <button onClick={() => setShowFailDialog(true)} className="rounded-md h-9 px-4 text-sm font-medium bg-destructive text-white shadow-xs hover:bg-destructive/90 disabled:opacity-50">
                  {t('page.shipment_detail.fail')}
                </button>
                <button onClick={() => setShowCancelDialog(true)} className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50">
                  {t('page.shipment_detail.cancel')}
                </button>
              </>
            )}
            {isDelivered && (
              <button
                onClick={() => navigate(`/shipments/new?return_for=${shipment.id}`)}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
              >
                {t('page.shipment_detail.create_return')}
              </button>
            )}
          </div>

          {showDispatchForm && (
            <div className="mt-3 bg-primary/10 rounded-lg p-3 space-y-3">
              <p className="text-xs text-muted-foreground">{t('page.shipment_detail.dispatch_form')}</p>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block mb-1.5 text-muted-foreground">{t('page.shipment_detail.carrier')}</label>
                  <input
                    value={dispatchCarrier}
                    onChange={(e) => setDispatchCarrier(e.target.value)}
                    className="w-full"
                  />
                </div>
                <div>
                  <label className="block mb-1.5 text-muted-foreground">{t('page.shipment_detail.tracking')}</label>
                  <input
                    value={dispatchTracking}
                    onChange={(e) => setDispatchTracking(e.target.value)}
                    className="w-full"
                  />
                </div>
              </div>
              <button
                onClick={() => dispatch.mutate()}
                disabled={!dispatchCarrier.trim() || dispatch.isPending}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50 disabled:opacity-50"
              >
                {t('page.shipment_detail.dispatch')}
              </button>
            </div>
          )}

          {showFailDialog && (
            <div className="mt-3 bg-destructive/10 rounded-lg p-3 space-y-3">
              <p className="text-xs text-destructive font-medium">{t('page.shipment_detail.fail_reason')}</p>
              <input
                value={failReason}
                onChange={(e) => setFailReason(e.target.value)}
                placeholder={t('page.shipment_detail.fail_reason')}
                className="w-full"
              />
              <div className="flex gap-2">
                <button
                  onClick={() => fail.mutate()}
                  disabled={!failReason.trim() || fail.isPending}
                  className="rounded-md h-9 px-4 text-sm font-medium bg-destructive text-white shadow-xs hover:bg-destructive/90 disabled:opacity-50"
                >
                  {t('page.shipment_detail.fail')}
                </button>
                <button onClick={() => { setShowFailDialog(false); setFailReason(''); }} className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50">
                  {t('common.cancel')}
                </button>
              </div>
            </div>
          )}

          {showCancelDialog && (
            <div className="mt-3 bg-secondary rounded-lg p-3 space-y-3">
              <p className="text-xs text-foreground font-medium">{t('page.shipment_detail.cancel_reason')}</p>
              <input
                value={cancelReason}
                onChange={(e) => setCancelReason(e.target.value)}
                placeholder={t('page.shipment_detail.cancel_reason')}
                className="w-full"
              />
              <div className="flex gap-2">
                <button
                  onClick={() => cancel.mutate()}
                  disabled={!cancelReason.trim() || cancel.isPending}
                  className="rounded-md h-9 px-4 text-sm font-medium bg-destructive text-white shadow-xs hover:bg-destructive/90 disabled:opacity-50"
                >
                  {t('page.shipment_detail.cancel')}
                </button>
                <button onClick={() => { setShowCancelDialog(false); setCancelReason(''); }} className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50">
                  {t('common.cancel')}
                </button>
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
