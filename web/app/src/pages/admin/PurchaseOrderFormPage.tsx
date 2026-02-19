import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { Card } from '../../components/ui/Card';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../lib/i18n';
import type { PurchaseOrder, Vendor, Department, PaginatedResponse } from '../../types';

interface ItemForm {
  description: string;
  asset_type: string;
  quantity: number;
  unit_cost_cents: number;
  notes: string;
}

const EMPTY_ITEM: ItemForm = { description: '', asset_type: '', quantity: 1, unit_cost_cents: 0, notes: '' };

export default function PurchaseOrderFormPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const { t } = useI18n();
  const isEdit = Boolean(id);

  const [vendorId, setVendorId] = useState('');
  const [vendorName, setVendorName] = useState('');
  const [departmentId, setDepartmentId] = useState('');
  const [notes, setNotes] = useState('');
  const [items, setItems] = useState<ItemForm[]>([{ ...EMPTY_ITEM }]);
  const [loaded, setLoaded] = useState(false);

  const { data: vendorsData } = useQuery({
    queryKey: ['vendors-active'],
    queryFn: async () => {
      const { data } = await api.get('/vendors?page_size=100&is_active=true');
      return data as PaginatedResponse<Vendor>;
    },
  });

  const { data: deptsData } = useQuery({
    queryKey: ['departments'],
    queryFn: async () => {
      const { data } = await api.get('/departments');
      return data as PaginatedResponse<Department>;
    },
  });

  const { data: deptBudget } = useQuery({
    queryKey: ['dept-budget', departmentId],
    queryFn: async () => {
      const { data } = await api.get(`/departments/${departmentId}/budget`);
      return data.data as { allocated_amount_cents: number; spent_cents: number; remaining_cents: number };
    },
    enabled: Boolean(departmentId),
    retry: false,
  });

  const vendors = vendorsData?.data ?? [];
  const departments = deptsData?.data ?? [];

  const { isLoading: poLoading } = useQuery({
    queryKey: ['purchase-order', id],
    queryFn: async () => {
      const { data } = await api.get(`/purchase-orders/${id}`);
      return data.data as PurchaseOrder;
    },
    enabled: isEdit && !loaded,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ...({ onSuccess: (po: PurchaseOrder) => {
      setVendorId(po.vendor_id || '');
      setVendorName(po.vendor_name);
      setDepartmentId(po.department_id);
      setNotes(po.notes || '');
      setItems(po.items.map((i) => ({
        description: i.description,
        asset_type: i.asset_type || '',
        quantity: i.quantity,
        unit_cost_cents: i.unit_cost_cents,
        notes: i.notes || '',
      })));
      setLoaded(true);
    }} as Record<string, unknown>),
  });

  // When editing and data isn't loaded via onSuccess (React Query v5), use effect-like approach
  const { data: existingPo } = useQuery({
    queryKey: ['purchase-order-edit', id],
    queryFn: async () => {
      const { data } = await api.get(`/purchase-orders/${id}`);
      return data.data as PurchaseOrder;
    },
    enabled: isEdit && !loaded,
  });

  if (isEdit && existingPo && !loaded) {
    setVendorId(existingPo.vendor_id || '');
    setVendorName(existingPo.vendor_name);
    setDepartmentId(existingPo.department_id);
    setNotes(existingPo.notes || '');
    setItems(existingPo.items.map((i) => ({
      description: i.description,
      asset_type: i.asset_type || '',
      quantity: i.quantity,
      unit_cost_cents: i.unit_cost_cents,
      notes: i.notes || '',
    })));
    setLoaded(true);
  }

  const handleVendorSelect = (selectedId: string) => {
    setVendorId(selectedId);
    const v = vendors.find((v) => v.id === selectedId);
    if (v) setVendorName(v.name);
  };

  const addItem = () => setItems([...items, { ...EMPTY_ITEM }]);
  const removeItem = (idx: number) => setItems(items.filter((_, i) => i !== idx));
  const updateItem = (idx: number, field: keyof ItemForm, value: string | number) => {
    setItems(items.map((item, i) => i === idx ? { ...item, [field]: value } : item));
  };

  const totalCents = items.reduce((sum, i) => sum + (i.quantity * i.unit_cost_cents), 0);

  const save = useMutation({
    mutationFn: async () => {
      const payload = {
        vendor_id: vendorId || null,
        vendor_name: vendorName,
        department_id: departmentId,
        items: items.map((i) => ({
          description: i.description,
          asset_type: i.asset_type || null,
          quantity: i.quantity,
          unit_cost_cents: i.unit_cost_cents,
          notes: i.notes || null,
        })),
        request_ids: [],
        notes: notes || null,
      };
      if (isEdit) {
        const { data } = await api.put(`/purchase-orders/${id}`, payload);
        return data.data;
      }
      const { data } = await api.post('/purchase-orders', payload);
      return data.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['purchase-orders'] });
      showToast({ title: isEdit ? t('page.po.toast_updated') : t('page.po.toast_created'), variant: 'success' });
      navigate(`/purchase-orders/${data.id}`);
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '';
      showToast({ title: isEdit ? t('page.po.error_update') : t('page.po.error_create'), description: detail, variant: 'error' });
    },
  });

  const canSubmit = vendorName.trim() && departmentId && items.length > 0 && items.every((i) => i.description.trim());

  if (isEdit && poLoading && !loaded) return <Loading />;

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-5">
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">
          {isEdit ? t('page.po.edit_po') : t('page.po.new_po')}
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">{t('page.po.subtitle')}</p>
      </div>

      <form onSubmit={(e) => { e.preventDefault(); save.mutate(); }} className="space-y-5">
        <Card className="overflow-hidden p-0">
          <div className="border-b border-border px-5 py-3.5">
            <h3 className="text-sm font-medium text-foreground">{t('page.po.order_info')}</h3>
          </div>
          <div className="grid grid-cols-1 gap-4 p-5 md:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-sm text-muted-foreground">{t('page.po.vendor')}</label>
              <select
                value={vendorId}
                onChange={(e) => handleVendorSelect(e.target.value)}
                className="w-full bg-card"
              >
                <option value="">{t('page.po.select_vendor')}</option>
                {vendors.map((v) => (
                  <option key={v.id} value={v.id}>{v.name}</option>
                ))}
              </select>
              <input
                value={vendorName}
                onChange={(e) => setVendorName(e.target.value)}
                placeholder={t('page.po.vendor_name_placeholder')}
                required
                maxLength={200}
                className="mt-2 w-full bg-card"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-sm text-muted-foreground">{t('page.po.department')}</label>
              <select
                value={departmentId}
                onChange={(e) => setDepartmentId(e.target.value)}
                required
                className="w-full bg-card"
              >
                <option value="">{t('page.po.select_department')}</option>
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
              {departmentId && deptBudget ? (
                <p className={`mt-1 text-xs ${deptBudget.remaining_cents < 0 ? 'text-destructive' : 'text-success'}`}>
                  {deptBudget.remaining_cents < 0
                    ? t('page.po.budget_over', { amount: (Math.abs(deptBudget.remaining_cents) / 100).toFixed(2) })
                    : t('page.po.budget_remaining', {
                        remaining: (deptBudget.remaining_cents / 100).toLocaleString(undefined, { minimumFractionDigits: 2 }),
                        allocated: (deptBudget.allocated_amount_cents / 100).toLocaleString(undefined, { minimumFractionDigits: 2 }),
                      })}
                </p>
              ) : departmentId ? (
                <p className="mt-1 text-xs text-muted-foreground">{t('page.po.no_budget_set')}</p>
              ) : null}
            </div>

            <div className="md:col-span-2">
              <label className="mb-1.5 block text-sm text-muted-foreground">{t('page.po.notes')}</label>
              <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={3} className="w-full resize-none bg-card" />
            </div>
          </div>
        </Card>

        <Card className="overflow-hidden p-0">
          <div className="flex items-center justify-between border-b border-border px-5 py-3.5">
            <h3 className="text-sm font-medium text-foreground">{t('page.po.items_detail')}</h3>
            <button
              type="button"
              onClick={addItem}
              className="inline-flex items-center justify-center gap-1.5 rounded-md h-8 px-3 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all"
            >
              <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M5 12h14M12 5v14" />
              </svg>
              {t('page.po.add_item')}
            </button>
          </div>

          <div className="divide-y divide-border">
            {items.map((item, idx) => {
              const lineTotal = item.quantity * item.unit_cost_cents;
              return (
                <div key={idx} className="p-5">
                  <div className="mb-3 flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">#{idx + 1}</span>
                    {items.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeItem(idx)}
                        className="inline-flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground hover:bg-accent hover:text-destructive transition-colors"
                        aria-label={t('page.po.remove_item')}
                        title={t('page.po.remove_item')}
                      >
                        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M3 6h18" />
                          <path d="M8 6V4h8v2" />
                          <path d="M19 6l-1 14H6L5 6" />
                          <path d="M10 11v6M14 11v6" />
                        </svg>
                      </button>
                    )}
                  </div>

                  <div className="grid grid-cols-1 gap-3 md:grid-cols-12">
                    <div className="md:col-span-5">
                      <label className="mb-1 block text-xs text-muted-foreground">{t('page.po.item_desc')}</label>
                      <input
                        value={item.description}
                        onChange={(e) => updateItem(idx, 'description', e.target.value)}
                        placeholder={t('page.po.item_desc')}
                        required
                        maxLength={500}
                        className="w-full bg-card"
                      />
                    </div>

                    <div className="md:col-span-3">
                      <label className="mb-1 block text-xs text-muted-foreground">{t('page.po.item_type')}</label>
                      <select
                        value={item.asset_type}
                        onChange={(e) => updateItem(idx, 'asset_type', e.target.value)}
                        className="w-full bg-card"
                      >
                        <option value="">{t('page.po.item_type')}</option>
                        {['laptop', 'desktop', 'phone', 'tablet', 'monitor', 'printer', 'other'].map((at) => (
                          <option key={at} value={at}>{t(`enum.${at}`, undefined, { defaultValue: at })}</option>
                        ))}
                      </select>
                    </div>

                    <div className="md:col-span-1">
                      <label className="mb-1 block text-xs text-muted-foreground">{t('page.po.item_qty')}</label>
                      <input
                        type="number"
                        min={1}
                        value={item.quantity}
                        onChange={(e) => updateItem(idx, 'quantity', parseInt(e.target.value) || 1)}
                        className="w-full bg-card"
                      />
                    </div>

                    <div className="md:col-span-2">
                      <label className="mb-1 block text-xs text-muted-foreground">{t('page.po.item_unit_cost')}</label>
                      <input
                        type="number"
                        min={0}
                        step={0.01}
                        value={item.unit_cost_cents / 100}
                        onChange={(e) => updateItem(idx, 'unit_cost_cents', Math.round(parseFloat(e.target.value || '0') * 100))}
                        className="w-full bg-card"
                      />
                    </div>

                    <div className="md:col-span-1">
                      <label className="mb-1 block text-xs text-muted-foreground">{t('page.po.item_total')}</label>
                      <div className="flex h-9 items-center rounded-md bg-muted px-3 text-sm font-medium text-foreground">
                        ${(lineTotal / 100).toFixed(2)}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="flex items-center justify-end border-t border-border px-5 py-3.5">
            <div className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground">{t('page.po.total')}:</span>
              <span className="text-lg font-semibold text-foreground">${(totalCents / 100).toFixed(2)}</span>
            </div>
          </div>
        </Card>

        <div className="flex items-center justify-end gap-3">
          <button type="button" onClick={() => navigate(-1)} className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all">
            {t('common.cancel')}
          </button>
          <button
            type="submit"
            disabled={save.isPending || !canSubmit}
            className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
          >
            {save.isPending ? t('common.working') : isEdit ? t('common.save') : t('page.po.save_draft')}
          </button>
        </div>
      </form>
    </div>
  );
}
