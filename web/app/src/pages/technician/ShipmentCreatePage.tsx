import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../lib/i18n';
import api from '../../lib/api';
import type { Asset, AssignableUser, PaginatedResponse, ShippingAddress } from '../../types';

type AddressMode = 'employee' | 'address' | 'here';
type ServiceLevel = 'standard' | 'two_day' | 'overnight';

/* ------------------------------------------------------------------ */
/* Small UI helpers                                                    */
/* ------------------------------------------------------------------ */

function SegmentControl({
  options,
  value,
  onChange,
}: {
  options: { value: string; label: string }[];
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="grid gap-1 rounded-lg bg-secondary/70 p-1" style={{ gridTemplateColumns: `repeat(${options.length}, 1fr)` }}>
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          onClick={() => onChange(opt.value)}
          className={
            value === opt.value
              ? 'flex items-center justify-center rounded-md bg-card px-3 py-1.5 text-sm font-medium text-primary shadow-sm transition-all'
              : 'flex items-center justify-center rounded-md px-3 py-1.5 text-sm font-medium text-muted-foreground transition-all hover:text-foreground'
          }
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

function SectionIcon({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex h-5 w-5 items-center justify-center text-primary">
      {children}
    </span>
  );
}

type InlineAddrFields = { label: string; street_line_1: string; street_line_2: string; city: string; state: string; postal_code: string; country: string };

function InlineAddressForm({
  addr,
  onChange,
  onActivate,
  active,
  t,
}: {
  addr: InlineAddrFields;
  onChange: (v: InlineAddrFields) => void;
  onActivate: () => void;
  active: boolean;
  t: (k: string) => string;
}) {
  const set = (field: keyof InlineAddrFields, value: string) => {
    if (!active) onActivate();
    onChange({ ...addr, [field]: value });
  };

  return (
    <div className="space-y-3 rounded-lg border border-dashed border-primary/40 bg-primary/5 p-4">
      <p className="text-xs font-medium uppercase tracking-wider text-primary">{t('page.shipment_create.new_address')}</p>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <label className="mb-1 block text-sm font-medium text-muted-foreground">{t('page.shipment_create.addr_street')}</label>
          <input value={addr.street_line_1} onChange={(e) => set('street_line_1', e.target.value)} className="w-full" placeholder="123 Main St" />
        </div>
        <div className="sm:col-span-2">
          <label className="mb-1 block text-sm font-medium text-muted-foreground">{t('page.shipment_create.addr_street_2')}</label>
          <input value={addr.street_line_2} onChange={(e) => set('street_line_2', e.target.value)} className="w-full" placeholder="Apt, Suite, Floor..." />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-muted-foreground">{t('page.shipment_create.addr_city')}</label>
          <input value={addr.city} onChange={(e) => set('city', e.target.value)} className="w-full" />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-muted-foreground">{t('page.shipment_create.addr_state')}</label>
          <input value={addr.state} onChange={(e) => set('state', e.target.value)} className="w-full" />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-muted-foreground">{t('page.shipment_create.addr_postal')}</label>
          <input value={addr.postal_code} onChange={(e) => set('postal_code', e.target.value)} className="w-full" />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-muted-foreground">{t('page.shipment_create.addr_country')}</label>
          <input value={addr.country} onChange={(e) => set('country', e.target.value)} className="w-full" />
        </div>
      </div>
    </div>
  );
}

function formatAddressOption(address: ShippingAddress): string {
  return `${address.label} — ${address.city}, ${address.state}`;
}

function formatAddressBlock(address: ShippingAddress): string {
  const line2 = address.street_line_2 ? `${address.street_line_2}, ` : '';
  return `${address.street_line_1}, ${line2}${address.city}, ${address.state} ${address.postal_code}, ${address.country}`;
}

/* ------------------------------------------------------------------ */
/* Main component                                                      */
/* ------------------------------------------------------------------ */

export default function ShipmentCreatePage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const returnFor = searchParams.get('return_for');
  const requestId = searchParams.get('request_id');
  const { t } = useI18n();
  const { showToast } = useToast();

  /* ---- State ---- */
  const direction = returnFor ? 'INBOUND' : 'OUTBOUND';
  const [destType, setDestType] = useState<'EMPLOYEE_HOME' | 'OFFICE' | 'VENDOR'>('EMPLOYEE_HOME');
  const [originMode, setOriginMode] = useState<AddressMode>('address');
  const [destinationMode, setDestinationMode] = useState<AddressMode>('employee');
  const [originUserId, setOriginUserId] = useState('');
  const [recipientUserId, setRecipientUserId] = useState('');
  const [originAddrId, setOriginAddrId] = useState('');
  const [destAddrId, setDestAddrId] = useState('');
  const [carrier, setCarrier] = useState('');
  const [serviceLevel, setServiceLevel] = useState<ServiceLevel>('standard');
  const [trackingNumber, setTrackingNumber] = useState('');
  const [trackingUrl, setTrackingUrl] = useState('');
  const [recipientName, setRecipientName] = useState('');
  const [itemsDescription, setItemsDescription] = useState('');
  const [internalNotes, setInternalNotes] = useState('');
  const [saveEmployeeAddress] = useState(false);
  const [selectedAssets, setSelectedAssets] = useState<string[]>([]);
  const [assetSearch, setAssetSearch] = useState('');
  const [formError, setFormError] = useState('');
  const [employeeModalTarget, setEmployeeModalTarget] = useState<'origin' | 'destination' | null>(null);
  const [employeeSearch, setEmployeeSearch] = useState('');

  // Inline address fields (when employee has no saved address)
  const [inlineAddr, setInlineAddr] = useState({ label: '', street_line_1: '', street_line_2: '', city: '', state: '', postal_code: '', country: 'US' });
  const [inlineAddrTarget, setInlineAddrTarget] = useState<'origin' | 'destination' | null>(null);
  const inlineAddrValid = inlineAddr.street_line_1.trim() && inlineAddr.city.trim() && inlineAddr.state.trim() && inlineAddr.postal_code.trim();

  /* ---- Queries ---- */
  const addressesQuery = useQuery({
    queryKey: ['addresses-all'],
    queryFn: async () => {
      const { data } = await api.get('/addresses', { params: { page_size: 100, is_active: true } });
      return data as PaginatedResponse<ShippingAddress>;
    },
  });

  const usersQuery = useQuery({
    queryKey: ['shipment-assignable-users'],
    queryFn: async () => {
      const { data } = await api.get('/assets/assignable-users');
      return data.data as AssignableUser[];
    },
  });

  const assetsQuery = useQuery({
    queryKey: ['assets-for-shipment'],
    queryFn: async () => {
      const { data } = await api.get('/assets', { params: { page_size: 100 } });
      return data as PaginatedResponse<Asset>;
    },
  });

  const addrList = addressesQuery.data?.data ?? [];
  const userList = usersQuery.data ?? [];
  const assetList = assetsQuery.data?.data ?? [];

  const officeAddresses = addrList.filter((a) => a.is_office);
  const companyAddressId = officeAddresses[0]?.id ?? '';
  const selectedOriginUser = userList.find((u) => u.id === originUserId);
  const selectedRecipientUser = userList.find((u) => u.id === recipientUserId);

  const originOptions = originMode === 'employee'
    ? (originUserId ? addrList.filter((a) => !a.is_office && a.user_id === originUserId) : addrList.filter((a) => !a.is_office))
    : originMode === 'here'
      ? officeAddresses
      : addrList;

  const destinationOptions = (
    destinationMode === 'employee' && recipientUserId
      ? addrList.filter((a) => !a.is_office && a.user_id === recipientUserId)
      : destinationMode === 'employee'
        ? addrList.filter((a) => !a.is_office)
        : destinationMode === 'here'
          ? officeAddresses
          : addrList
  );

  const resolvedOriginAddrId = originMode === 'here' ? (originAddrId || companyAddressId) : originAddrId;
  const resolvedDestAddrId = destinationMode === 'here' ? (destAddrId || companyAddressId) : destAddrId;

  const effectiveDestinationType: 'EMPLOYEE_HOME' | 'OFFICE' | 'VENDOR' = (
    destinationMode === 'employee' ? 'EMPLOYEE_HOME' : destinationMode === 'here' ? 'OFFICE' : destType
  );

  const filteredAssets = assetSearch
    ? assetList.filter((a) =>
        a.brand.toLowerCase().includes(assetSearch.toLowerCase()) ||
        a.model.toLowerCase().includes(assetSearch.toLowerCase()) ||
        a.serial_number.toLowerCase().includes(assetSearch.toLowerCase()),
      )
    : assetList;

  const employeeSearchNormalized = employeeSearch.trim().toLowerCase();
  const filteredEmployees = employeeSearchNormalized
    ? userList.filter((u) => `${u.email} ${u.name ?? ''}`.toLowerCase().includes(employeeSearchNormalized))
    : userList;

  // Derived flags: does the selected employee need an inline address?
  const originNeedsInline = originMode === 'employee' && originUserId && !originOptions.length;
  const destNeedsInline = destinationMode === 'employee' && recipientUserId && !destinationOptions.length;

  /* ---- Mutation ---- */
  const createShipment = useMutation({
    mutationFn: async () => {
      let finalOriginAddrId = resolvedOriginAddrId;
      let finalDestAddrId = resolvedDestAddrId;

      // Create inline address if employee has none
      if (inlineAddrTarget && inlineAddrValid) {
        const userId = inlineAddrTarget === 'origin' ? originUserId : recipientUserId;
        const addrPayload = {
          ...inlineAddr,
          label: inlineAddr.label || `${inlineAddr.city}, ${inlineAddr.state}`,
          user_id: userId || undefined,
          is_office: false,
        };
        const { data: addrResp } = await api.post('/addresses', addrPayload);
        const newAddrId = addrResp.data.id as string;
        if (inlineAddrTarget === 'origin') finalOriginAddrId = newAddrId;
        else finalDestAddrId = newAddrId;
      }

      const payload: Record<string, unknown> = {
        direction,
        destination_type: effectiveDestinationType,
        asset_ids: selectedAssets,
      };

      if (finalOriginAddrId) payload.origin_address_id = finalOriginAddrId;
      if (finalDestAddrId) payload.destination_address_id = finalDestAddrId;
      if (destinationMode === 'employee' && recipientUserId) payload.recipient_user_id = recipientUserId;
      if (carrier) payload.carrier = carrier;
      if (serviceLevel) payload.service_level = serviceLevel;
      if (trackingNumber) payload.tracking_number = trackingNumber;
      if (trackingUrl) payload.tracking_url = trackingUrl;
      if (recipientName) payload.recipient_name = recipientName;
      if (itemsDescription.trim()) payload.items_description = itemsDescription.trim();
      if (internalNotes.trim()) payload.internal_notes = internalNotes.trim();
      if (internalNotes.trim()) payload.notes = internalNotes.trim();
      if (saveEmployeeAddress && destinationMode === 'employee') {
        payload.notes = `${(payload.notes as string | undefined) ?? ''}\n[REQUEST] update_employee_address=true`.trim();
      }

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
      showToast({ title: t('page.shipment_create.error_create'), description: detail, variant: 'error', durationMs: 5000 });
    },
  });

  /* ---- Handlers ---- */
  const toggleAsset = (assetId: string) => {
    if (formError) setFormError('');
    setSelectedAssets((prev) =>
      prev.includes(assetId) ? prev.filter((id) => id !== assetId) : [...prev, assetId],
    );
  };

  const openEmployeeModal = (target: 'origin' | 'destination') => {
    setEmployeeModalTarget(target);
    setEmployeeSearch('');
  };

  const closeEmployeeModal = () => {
    setEmployeeModalTarget(null);
    setEmployeeSearch('');
  };

  const chooseEmployee = (userId: string) => {
    if (employeeModalTarget === 'origin') {
      setOriginUserId(userId);
      setOriginAddrId('');
    }
    if (employeeModalTarget === 'destination') {
      setRecipientUserId(userId);
      setDestAddrId('');
    }
    setFormError('');
    closeEmployeeModal();
  };

  const setOriginToHere = () => { setOriginMode('here'); setOriginUserId(''); setOriginAddrId(companyAddressId); setFormError(''); };
  const setOriginToEmployee = () => {
    const was = originMode === 'employee';
    setOriginMode('employee');
    if (!was) { setOriginAddrId(''); setOriginUserId(''); }
    setFormError('');
    openEmployeeModal('origin');
  };
  const setOriginToAddress = () => { setOriginMode('address'); setOriginAddrId(''); setOriginUserId(''); setFormError(''); };
  const setDestinationToHere = () => { setDestinationMode('here'); setDestType('OFFICE'); setRecipientUserId(''); setDestAddrId(companyAddressId); setFormError(''); };
  const setDestinationToEmployee = () => {
    const was = destinationMode === 'employee';
    setDestinationMode('employee');
    setDestType('EMPLOYEE_HOME');
    if (!was) { setDestAddrId(''); setRecipientUserId(''); }
    setFormError('');
    openEmployeeModal('destination');
  };
  const setDestinationToAddress = () => { setDestinationMode('address'); setDestType('VENDOR'); setRecipientUserId(''); setDestAddrId(''); setFormError(''); };

  const handleOriginModeChange = (v: string) => {
    if (v === 'here') setOriginToHere();
    else if (v === 'employee') setOriginToEmployee();
    else setOriginToAddress();
  };

  const handleDestModeChange = (v: string) => {
    if (v === 'here') setDestinationToHere();
    else if (v === 'employee') setDestinationToEmployee();
    else setDestinationToAddress();
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setFormError('');
    const showValidationError = (msg: string) => {
      setFormError(msg);
      showToast({ title: t('page.shipment_create.validation_error'), description: msg, variant: 'error', durationMs: 5000 });
    };
    if (!selectedAssets.length) { showValidationError(t('page.shipment_create.error_assets_required')); return; }
    if (destinationMode === 'employee' && !recipientUserId) { showValidationError(t('page.shipment_create.error_employee_required')); return; }
    if (destinationMode === 'here' && !companyAddressId && !destAddrId) { showValidationError(t('page.shipment_create.error_company_address_required')); return; }
    // Allow inline address as a valid destination
    const hasInlineAddr = inlineAddrTarget && inlineAddrValid;
    if (!resolvedDestAddrId && !hasInlineAddr) { showValidationError(t('page.shipment_create.error_destination_required')); return; }
    createShipment.mutate();
  };

  /* ---------------------------------------------------------------- */
  /* Render                                                            */
  /* ---------------------------------------------------------------- */

  return (
    <div className="mx-auto max-w-[1280px] pb-12">

      {/* Breadcrumbs */}
      <nav className="mb-6 flex" aria-label="Breadcrumb">
        <ol className="inline-flex items-center gap-1 text-sm">
          <li><Link to="/" className="text-muted-foreground hover:text-primary">Home</Link></li>
          <li className="text-muted-foreground">/</li>
          <li><Link to="/shipments" className="text-muted-foreground hover:text-primary">{t('page.shipments.title')}</Link></li>
          <li className="text-muted-foreground">/</li>
          <li className="font-medium text-primary">{t('page.shipment_create.title')}</li>
        </ol>
      </nav>

      {/* Page header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">{t('page.shipment_create.title')}</h1>
        <p className="mt-2 text-muted-foreground">{t('page.shipment_create.subtitle')}</p>
      </div>

      {/* Linked request / return info */}
      {(requestId || returnFor) && (
        <div className="mb-6 flex flex-wrap gap-3">
          {requestId && (
            <div className="inline-flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-sm">
              <span className="text-muted-foreground">{t('page.shipment_create.linked_request')}:</span>
              <span className="font-mono text-xs text-foreground">{requestId}</span>
            </div>
          )}
          {returnFor && (
            <div className="inline-flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-sm">
              <span className="text-muted-foreground">{t('page.shipment_create.return_for')}:</span>
              <span className="font-mono text-xs text-foreground">{returnFor}</span>
            </div>
          )}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {formError && (
          <div className="rounded-lg border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {formError}
          </div>
        )}

        {/* Employee selection modal */}
        {employeeModalTarget && (
          <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
            <button
              type="button"
              className="absolute inset-0 bg-black/40"
              onClick={closeEmployeeModal}
              aria-label={t('errors.close_confirmation_dialog')}
            />
            <div className="relative z-[91] w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-lg">
              <h3 className="text-lg font-semibold text-foreground">
                {employeeModalTarget === 'origin' ? t('page.shipment_create.select_origin_employee') : t('page.shipment_create.select_destination_employee')}
              </h3>
              <div className="mt-4">
                <input
                  type="search"
                  value={employeeSearch}
                  onChange={(e) => setEmployeeSearch(e.target.value)}
                  placeholder={t('page.shipment_create.search_employee')}
                  className="w-full"
                />
              </div>
              <div className="mt-3 max-h-72 overflow-auto rounded-lg border border-border">
                {usersQuery.isLoading ? (
                  <p className="px-4 py-3 text-sm text-muted-foreground">{t('page.addresses.loading_users')}</p>
                ) : filteredEmployees.length === 0 ? (
                  <p className="px-4 py-3 text-sm text-muted-foreground">{t('page.shipment_create.no_employee_match')}</p>
                ) : (
                  filteredEmployees.map((u) => (
                    <button
                      key={u.id}
                      type="button"
                      onClick={() => chooseEmployee(u.id)}
                      className="flex w-full items-center justify-between border-b border-border/50 px-4 py-2.5 text-left text-sm text-foreground hover:bg-accent last:border-b-0"
                    >
                      <span className="truncate font-medium">{u.name || u.email}</span>
                      <span className="ml-3 text-xs text-muted-foreground">{u.email}</span>
                    </button>
                  ))
                )}
              </div>
              <div className="mt-4 flex justify-end">
                <button
                  type="button"
                  onClick={closeEmployeeModal}
                  className="rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium text-foreground shadow-sm hover:bg-accent transition-all"
                >
                  {t('common.cancel')}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ============================================================ */}
        {/* ORIGIN & DESTINATION — side by side                          */}
        {/* ============================================================ */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">

          {/* Origin card */}
          <section className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
            <div className="flex items-center justify-between border-b border-border bg-secondary/30 px-6 py-4">
              <h3 className="flex items-center gap-2 text-base font-semibold text-foreground">
                <SectionIcon>
                  <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="m4 18 8-8 8 8" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 10V4" />
                  </svg>
                </SectionIcon>
                {t('page.shipment_create.origin_sender')}
              </h3>
            </div>
            <div className="space-y-5 p-6">
              <SegmentControl
                options={[
                  { value: 'here', label: t('page.shipment_create.mode_current_office') },
                  { value: 'employee', label: t('page.shipment_create.destination_mode_employee') },
                  { value: 'address', label: t('page.shipment_create.mode_external') },
                ]}
                value={originMode}
                onChange={handleOriginModeChange}
              />

              {originMode === 'here' && (
                <div className="flex gap-4 rounded-lg border border-border bg-secondary/30 p-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21" />
                    </svg>
                  </div>
                  <div>
                    {officeAddresses[0] ? (
                      <>
                        <p className="text-sm font-semibold text-foreground">{officeAddresses[0].label}</p>
                        <p className="mt-1 text-sm text-muted-foreground">{formatAddressBlock(officeAddresses[0])}</p>
                      </>
                    ) : (
                      <p className="text-sm text-muted-foreground">{t('page.shipment_create.no_company_address')}</p>
                    )}
                  </div>
                </div>
              )}

              {originMode === 'employee' && (
                <div className="space-y-4">
                  {selectedOriginUser ? (
                    <>
                      <div className="flex items-center justify-between">
                        <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{t('page.shipment_create.selected_employee')}</p>
                        <button type="button" onClick={() => openEmployeeModal('origin')} className="text-xs font-medium text-primary hover:text-primary/80">{t('common.edit')}</button>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="mb-1 block text-sm font-medium text-muted-foreground">Name</label>
                          <input readOnly value={selectedOriginUser.name || selectedOriginUser.email} className="w-full cursor-not-allowed bg-secondary/50" />
                        </div>
                        <div>
                          <label className="mb-1 block text-sm font-medium text-muted-foreground">Email</label>
                          <input readOnly value={selectedOriginUser.email} className="w-full cursor-not-allowed bg-secondary/50" />
                        </div>
                      </div>
                    </>
                  ) : (
                    <button
                      type="button"
                      onClick={() => openEmployeeModal('origin')}
                      className="flex w-full items-center justify-center gap-2 rounded-lg border-2 border-dashed border-border py-4 text-sm text-muted-foreground hover:border-primary hover:text-primary transition-colors"
                    >
                      <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0" /></svg>
                      {t('page.shipment_create.select_employee')}
                    </button>
                  )}
                </div>
              )}

              <div>
                <label className="mb-1.5 block text-sm font-medium text-muted-foreground">{t('page.shipment_create.origin_address')}</label>
                <select
                  value={inlineAddrTarget === 'origin' ? '__new__' : resolvedOriginAddrId}
                  onChange={(e) => {
                    if (e.target.value === '__new__') { setOriginAddrId(''); setInlineAddrTarget('origin'); setInlineAddr({ label: '', street_line_1: '', street_line_2: '', city: '', state: '', postal_code: '', country: 'US' }); }
                    else { setOriginAddrId(e.target.value); if (inlineAddrTarget === 'origin') setInlineAddrTarget(null); }
                    setFormError('');
                  }}
                  className="w-full"
                  disabled={addressesQuery.isLoading || (originMode === 'employee' && !originUserId)}
                >
                  <option value="">
                    {originMode === 'employee' && !originUserId
                      ? t('page.shipment_create.select_employee_first')
                      : addressesQuery.isLoading
                        ? t('page.shipment_create.loading_addresses')
                        : t('page.shipment_create.select_address')}
                  </option>
                  {originOptions.map((a) => (
                    <option key={a.id} value={a.id}>{formatAddressOption(a)}</option>
                  ))}
                  <option value="__new__">+ {t('page.shipment_create.new_address')}</option>
                </select>
              </div>
              {(originNeedsInline || inlineAddrTarget === 'origin') && (
                <InlineAddressForm
                  addr={inlineAddrTarget === 'origin' ? inlineAddr : { label: '', street_line_1: '', street_line_2: '', city: '', state: '', postal_code: '', country: 'US' }}
                  onChange={(v) => { setInlineAddr(v); setInlineAddrTarget('origin'); setFormError(''); }}
                  onActivate={() => setInlineAddrTarget('origin')}
                  active={inlineAddrTarget === 'origin'}
                  t={t}
                />
              )}
            </div>
          </section>

          {/* Destination card */}
          <section className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
            <div className="flex items-center justify-between border-b border-border bg-secondary/30 px-6 py-4">
              <h3 className="flex items-center gap-2 text-base font-semibold text-foreground">
                <SectionIcon>
                  <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="m20 6-8 8-8-8" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 14v6" />
                  </svg>
                </SectionIcon>
                {t('page.shipment_create.destination_receiver')}
              </h3>
            </div>
            <div className="space-y-5 p-6">
              <SegmentControl
                options={[
                  { value: 'here', label: t('page.shipment_create.mode_current_office') },
                  { value: 'employee', label: t('page.shipment_create.destination_mode_employee') },
                  { value: 'address', label: t('page.shipment_create.mode_external') },
                ]}
                value={destinationMode}
                onChange={handleDestModeChange}
              />

              {destinationMode === 'here' && (
                <div className="flex gap-4 rounded-lg border border-border bg-secondary/30 p-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21" />
                    </svg>
                  </div>
                  <div>
                    {officeAddresses[0] ? (
                      <>
                        <p className="text-sm font-semibold text-foreground">{officeAddresses[0].label}</p>
                        <p className="mt-1 text-sm text-muted-foreground">{formatAddressBlock(officeAddresses[0])}</p>
                      </>
                    ) : (
                      <p className="text-sm text-muted-foreground">{t('page.shipment_create.no_company_address')}</p>
                    )}
                  </div>
                </div>
              )}

              {destinationMode === 'employee' && (
                <div className="space-y-4">
                  {selectedRecipientUser ? (
                    <>
                      <div className="flex items-center justify-between">
                        <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{t('page.shipment_create.selected_employee')}</p>
                        <button type="button" onClick={() => openEmployeeModal('destination')} className="text-xs font-medium text-primary hover:text-primary/80">{t('common.edit')}</button>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="mb-1 block text-sm font-medium text-muted-foreground">Name</label>
                          <input readOnly value={selectedRecipientUser.name || selectedRecipientUser.email} className="w-full cursor-not-allowed bg-secondary/50" />
                        </div>
                        <div>
                          <label className="mb-1 block text-sm font-medium text-muted-foreground">Email</label>
                          <input readOnly value={selectedRecipientUser.email} className="w-full cursor-not-allowed bg-secondary/50" />
                        </div>
                      </div>
                    </>
                  ) : (
                    <button
                      type="button"
                      onClick={() => openEmployeeModal('destination')}
                      className="flex w-full items-center justify-center gap-2 rounded-lg border-2 border-dashed border-border py-4 text-sm text-muted-foreground hover:border-primary hover:text-primary transition-colors"
                    >
                      <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0" /></svg>
                      {t('page.shipment_create.select_employee')}
                    </button>
                  )}
                </div>
              )}

              <div>
                <label className="mb-1.5 block text-sm font-medium text-muted-foreground">{t('page.shipment_create.destination_address')}</label>
                <select
                  value={inlineAddrTarget === 'destination' ? '__new__' : resolvedDestAddrId}
                  onChange={(e) => {
                    if (e.target.value === '__new__') { setDestAddrId(''); setInlineAddrTarget('destination'); setInlineAddr({ label: '', street_line_1: '', street_line_2: '', city: '', state: '', postal_code: '', country: 'US' }); }
                    else { setDestAddrId(e.target.value); if (inlineAddrTarget === 'destination') setInlineAddrTarget(null); }
                    setFormError('');
                  }}
                  className="w-full"
                  disabled={addressesQuery.isLoading || (destinationMode === 'employee' && !recipientUserId)}
                >
                  <option value="">
                    {destinationMode === 'employee' && !recipientUserId
                      ? t('page.shipment_create.select_employee_first')
                      : addressesQuery.isLoading
                        ? t('page.shipment_create.loading_addresses')
                        : t('page.shipment_create.select_address')}
                  </option>
                  {destinationOptions.map((a) => (
                    <option key={a.id} value={a.id}>{formatAddressOption(a)}</option>
                  ))}
                  <option value="__new__">+ {t('page.shipment_create.new_address')}</option>
                </select>
                {destinationMode === 'here' && !companyAddressId && (
                  <p className="mt-1.5 text-xs text-muted-foreground">{t('page.shipment_create.no_company_address')}</p>
                )}
              </div>
              {(destNeedsInline || inlineAddrTarget === 'destination') && (
                <InlineAddressForm
                  addr={inlineAddrTarget === 'destination' ? inlineAddr : { label: '', street_line_1: '', street_line_2: '', city: '', state: '', postal_code: '', country: 'US' }}
                  onChange={(v) => { setInlineAddr(v); setInlineAddrTarget('destination'); setFormError(''); }}
                  onActivate={() => setInlineAddrTarget('destination')}
                  active={inlineAddrTarget === 'destination'}
                  t={t}
                />
              )}
            </div>
          </section>
        </div>

        {/* ============================================================ */}
        {/* SHIPMENT LOGISTICS                                           */}
        {/* ============================================================ */}
        <section className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
          <div className="border-b border-border bg-secondary/30 px-6 py-4">
            <h3 className="flex items-center gap-2 text-base font-semibold text-foreground">
              <SectionIcon>
                <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="m20.25 7.5-.625 10.632a2.25 2.25 0 0 1-2.247 2.118H6.622a2.25 2.25 0 0 1-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125Z" />
                </svg>
              </SectionIcon>
              {t('page.shipment_create.section_shipping')}
            </h3>
          </div>
          <div className="grid grid-cols-1 gap-6 p-6 md:grid-cols-12">
            {/* Left: logistics info */}
            <div className="space-y-4 md:col-span-4">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-muted-foreground">{t('page.shipment_create.carrier')}</label>
                <input value={carrier} onChange={(e) => setCarrier(e.target.value)} className="w-full" placeholder="FedEx, UPS, DHL..." />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-muted-foreground">{t('page.shipment_create.service_level')}</label>
                <input value={serviceLevel} onChange={(e) => setServiceLevel(e.target.value as ServiceLevel)} className="w-full" placeholder="Standard, 24h, 48h..." />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-muted-foreground">
                  {t('page.shipment_create.tracking_number')} <span className="font-normal text-muted-foreground/60">(Optional)</span>
                </label>
                <input value={trackingNumber} onChange={(e) => setTrackingNumber(e.target.value)} className="w-full" placeholder="Enter tracking #" />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-muted-foreground">
                  {t('page.shipment_create.tracking_url')} <span className="font-normal text-muted-foreground/60">(Optional)</span>
                </label>
                <input value={trackingUrl} onChange={(e) => setTrackingUrl(e.target.value)} className="w-full" placeholder="https://..." />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-muted-foreground">{t('page.shipment_create.recipient_name')}</label>
                <input value={recipientName} onChange={(e) => setRecipientName(e.target.value)} className="w-full" />
              </div>
            </div>

            {/* Right: items & notes */}
            <div className="space-y-4 md:col-span-8">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-muted-foreground">{t('page.shipment_create.items_description')}</label>
                <div className="relative">
                  <textarea
                    value={itemsDescription}
                    onChange={(e) => setItemsDescription(e.target.value.slice(0, 500))}
                    rows={4}
                    maxLength={500}
                    className="w-full resize-none"
                    placeholder='List items here e.g., MacBook Pro 16 (Asset #1234), Dell Monitor 27", Docking Station...'
                  />
                  <span className="absolute bottom-2 right-3 text-xs text-muted-foreground">{itemsDescription.length}/500</span>
                </div>
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-muted-foreground">{t('page.shipment_create.internal_notes')}</label>
                <textarea
                  value={internalNotes}
                  onChange={(e) => setInternalNotes(e.target.value)}
                  rows={3}
                  className="w-full resize-none"
                  placeholder="Add private notes for the IT team (not visible on shipping label)..."
                />
              </div>
            </div>
          </div>
        </section>

        {/* ============================================================ */}
        {/* ASSETS                                                       */}
        {/* ============================================================ */}
        <section className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
          <div className="border-b border-border bg-secondary/30 px-6 py-4">
            <h3 className="flex items-center gap-2 text-base font-semibold text-foreground">
              <SectionIcon>
                <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 17.25v1.007a3 3 0 0 1-.879 2.122L7.5 21h9l-.621-.621A3 3 0 0 1 15 18.257V17.25m6-12V15a2.25 2.25 0 0 1-2.25 2.25H5.25A2.25 2.25 0 0 1 3 15V5.25A2.25 2.25 0 0 1 5.25 3h13.5A2.25 2.25 0 0 1 21 5.25Z" />
                </svg>
              </SectionIcon>
              {t('page.shipment_create.assets')}
              {selectedAssets.length > 0 && (
                <span className="ml-1 rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                  {t('page.shipment_create.selected_count', { count: selectedAssets.length })}
                </span>
              )}
            </h3>
          </div>

          <div className="space-y-4 p-6">
            {addressesQuery.isError && (
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                <span>{t('page.shipment_create.error_addresses_load')}</span>
                <button
                  type="button"
                  onClick={() => { void addressesQuery.refetch(); }}
                  className="rounded-md border border-destructive/30 bg-card px-3 py-1 text-xs font-medium text-foreground hover:bg-accent"
                >
                  {t('common.retry')}
                </button>
              </div>
            )}

            {assetsQuery.isError && (
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                <span>{t('page.shipment_create.error_assets_load')}</span>
                <button
                  type="button"
                  onClick={() => { void assetsQuery.refetch(); }}
                  className="rounded-md border border-destructive/30 bg-card px-3 py-1 text-xs font-medium text-foreground hover:bg-accent"
                >
                  {t('common.retry')}
                </button>
              </div>
            )}

            <input
              value={assetSearch}
              onChange={(e) => setAssetSearch(e.target.value)}
              placeholder={t('page.shipment_create.search_assets')}
              className="w-full"
            />

            <div className="overflow-hidden rounded-lg border border-border">
              {assetsQuery.isLoading ? (
                <p className="p-4 text-sm text-muted-foreground">{t('page.shipment_create.loading_assets')}</p>
              ) : filteredAssets.length === 0 ? (
                <p className="p-4 text-sm text-muted-foreground">{t('page.shipment_create.no_assets')}</p>
              ) : (
                <div className="max-h-72 overflow-auto">
                  <table className="w-full min-w-[680px] text-sm">
                    <thead>
                      <tr className="border-b border-border bg-secondary/40">
                        <th className="w-10 px-4 py-2 text-left font-medium text-foreground" />
                        <th className="px-4 py-2 text-left font-medium text-foreground">{t('table.asset')}</th>
                        <th className="px-4 py-2 text-left font-medium text-foreground">{t('table.serial')}</th>
                        <th className="px-4 py-2 text-left font-medium text-foreground">{t('table.status')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredAssets.map((asset) => (
                        <tr key={asset.id} className="border-t border-border hover:bg-accent/30">
                          <td className="px-4 py-2.5">
                            <input
                              type="checkbox"
                              checked={selectedAssets.includes(asset.id)}
                              onChange={() => toggleAsset(asset.id)}
                              className="h-4 w-4 rounded border-input text-primary focus:ring-primary"
                            />
                          </td>
                          <td className="px-4 py-2.5 font-medium text-foreground">{asset.brand} {asset.model}</td>
                          <td className="px-4 py-2.5 font-mono text-xs text-muted-foreground">{asset.serial_number}</td>
                          <td className="px-4 py-2.5 text-muted-foreground">
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
        </section>

        {/* ============================================================ */}
        {/* ACTIONS                                                      */}
        {/* ============================================================ */}
        <div className="flex items-center justify-end gap-4 border-t border-border pt-6">
          <button
            type="button"
            onClick={() => navigate('/shipments')}
            className="rounded-lg border border-border bg-card px-6 py-2.5 text-sm font-medium text-foreground shadow-sm transition-all hover:bg-accent"
          >
            {t('common.cancel')}
          </button>
          <button
            type="submit"
            disabled={createShipment.isPending}
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground shadow-sm transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
          >
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5" />
            </svg>
            {createShipment.isPending ? t('page.shipment_create.saving') : t('page.shipment_create.save_draft')}
          </button>
        </div>
      </form>
    </div>
  );
}
