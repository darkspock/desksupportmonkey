import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import api from '../../lib/api';
import { Card } from '../../components/ui/Card';
import { useI18n } from '../../lib/i18n';
import type { ImportPreviewResult, ImportConfirmResult, ImportDepartment } from '../../types';

type MappingAction = { action: 'create' } | { action: 'map'; department_id: string };
type RoleMappingAction = { action: 'create' } | { action: 'map'; employee_role_id: string };

type Step = 'upload' | 'preview' | 'result';

export default function UserImportPage() {
  const navigate = useNavigate();
  const { t } = useI18n();

  const [step, setStep] = useState<Step>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreviewResult | null>(null);
  const [deptMapping, setDeptMapping] = useState<Record<string, MappingAction>>({});
  const [roleMapping, setRoleMapping] = useState<Record<string, RoleMappingAction>>({});
  const [result, setResult] = useState<ImportConfirmResult | null>(null);

  // Escape key → back to users
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') navigate('/users');
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [navigate]);

  const previewMutation = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error(t('page.user_import.no_file'));
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await api.post('/users/import/preview', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return data.data as ImportPreviewResult;
    },
    onSuccess: (data) => {
      setPreview(data);
      const dm: Record<string, MappingAction> = {};
      for (const dept of data.unknown_departments) {
        dm[dept] = { action: 'create' };
      }
      setDeptMapping(dm);
      const rm: Record<string, RoleMappingAction> = {};
      for (const role of data.unknown_employee_roles) {
        rm[role] = { action: 'create' };
      }
      setRoleMapping(rm);
      setStep('preview');
    },
  });

  const confirmMutation = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error(t('page.user_import.no_file'));
      const formData = new FormData();
      formData.append('file', file);
      formData.append('department_mapping', JSON.stringify(deptMapping));
      formData.append('employee_role_mapping', JSON.stringify(roleMapping));
      const { data } = await api.post('/users/import/confirm', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return data.data as ImportConfirmResult;
    },
    onSuccess: (data) => {
      setResult(data);
      setStep('result');
    },
  });

  const allDeptsResolved = preview
    ? preview.unknown_departments.every((d) => {
        const m = deptMapping[d];
        if (!m) return false;
        if (m.action === 'map' && !m.department_id) return false;
        return true;
      })
    : true;

  const allRolesResolved = preview
    ? preview.unknown_employee_roles.every((r) => {
        const m = roleMapping[r];
        if (!m) return false;
        if (m.action === 'map' && !m.employee_role_id) return false;
        return true;
      })
    : true;

  const existingDepartments: ImportDepartment[] = preview?.existing_departments ?? [];
  const existingEmployeeRoles: ImportDepartment[] = preview?.existing_employee_roles ?? [];

  return (
    <div className="mx-auto max-w-2xl">
      <h2 className="text-2xl font-semibold tracking-tight text-foreground mb-1">{t('page.user_import.title')}</h2>
      <p className="text-sm text-muted-foreground mb-6">{t('page.user_import.help')}</p>

      <Card>
        {/* STEP 1: Upload */}
        {step === 'upload' && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              previewMutation.mutate();
            }}
            className="space-y-4"
          >
            <p className="text-sm text-muted-foreground">
              {t('page.user_import.help_roles')}{' '}
              <a
                href="/templates/user_import_template.csv"
                download="user_import_template.csv"
                className="text-primary underline hover:text-primary/80"
              >
                {t('page.user_import.download_template')}
              </a>
            </p>
            <div>
              <label className="mb-1.5 block text-sm text-muted-foreground">{t('page.user_import.select_file')}</label>
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="block w-full text-sm text-muted-foreground file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
              />
            </div>
            {previewMutation.isError && (
              <div className="bg-destructive/15 border border-destructive/20 rounded p-3">
                <p className="text-sm text-destructive">
                  {(previewMutation.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.user_import.error_preview')}
                </p>
              </div>
            )}
            <div className="flex gap-3">
              <button
                type="submit"
                disabled={!file || previewMutation.isPending}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
              >
                {previewMutation.isPending ? t('page.user_import.previewing') : t('page.user_import.preview')}
              </button>
              <button
                type="button"
                onClick={() => navigate('/users')}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
              >
                {t('common.cancel')}
              </button>
            </div>
          </form>
        )}

        {/* STEP 2: Preview */}
        {step === 'preview' && preview && (
          <div className="space-y-5">
            {/* Counts */}
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <div className="rounded-lg border border-border p-3 text-center">
                <p className="text-2xl font-semibold text-foreground">{preview.total_rows}</p>
                <p className="text-xs text-muted-foreground">{t('page.user_import.total_rows')}</p>
              </div>
              <div className="rounded-lg border border-border p-3 text-center">
                <p className="text-2xl font-semibold text-success">{preview.valid_rows}</p>
                <p className="text-xs text-muted-foreground">{t('page.user_import.valid_rows')}</p>
              </div>
              <div className="rounded-lg border border-border p-3 text-center">
                <p className="text-2xl font-semibold text-primary">{preview.new_users}</p>
                <p className="text-xs text-muted-foreground">{t('page.user_import.new_users')}</p>
              </div>
              {preview.existing_users > 0 && (
                <div className="rounded-lg border border-border p-3 text-center">
                  <p className="text-2xl font-semibold text-warning">{preview.existing_users}</p>
                  <p className="text-xs text-muted-foreground">{t('page.user_import.existing_users')}</p>
                </div>
              )}
            </div>

            {/* Row errors */}
            {preview.errors.length > 0 && (
              <div className="bg-destructive/15 border border-destructive/20 rounded p-3">
                <p className="text-sm font-medium text-destructive mb-2">
                  {t('page.user_import.row_errors')} ({t('page.user_import.errors_count', { count: preview.errors.length })})
                </p>
                <ul className="text-xs text-destructive list-disc pl-4 space-y-0.5">
                  {preview.errors.map((e, i) => (
                    <li key={i}>
                      <span className="font-medium">{t('page.user_import.row_n', { row: e.row })}</span>: {e.error}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Unknown departments mapping */}
            {preview.unknown_departments.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-foreground">{t('page.user_import.unknown_departments')}</h3>
                {preview.unknown_departments.map((dept) => {
                  const mapping = deptMapping[dept] ?? { action: 'create' as const };
                  return (
                    <div key={dept} className="rounded-lg border border-border p-3 space-y-2">
                      <p className="text-sm font-medium text-foreground">{dept}</p>
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                        <select
                          value={mapping.action}
                          onChange={(e) => {
                            const action = e.target.value as 'create' | 'map';
                            setDeptMapping((prev) => ({
                              ...prev,
                              [dept]: action === 'create' ? { action: 'create' } : { action: 'map', department_id: '' },
                            }));
                          }}
                          className="w-full sm:w-auto bg-card text-sm"
                        >
                          <option value="create">{t('page.user_import.dept_action_create')}</option>
                          <option value="map">{t('page.user_import.dept_action_map')}</option>
                        </select>
                        {mapping.action === 'map' && (
                          <select
                            value={mapping.department_id}
                            onChange={(e) => {
                              setDeptMapping((prev) => ({
                                ...prev,
                                [dept]: { action: 'map', department_id: e.target.value },
                              }));
                            }}
                            className="w-full sm:flex-1 bg-card text-sm"
                          >
                            <option value="">{t('page.user_import.select_department')}</option>
                            {existingDepartments.map((d) => (
                              <option key={d.id} value={d.id}>{d.name}</option>
                            ))}
                          </select>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Unknown employee roles mapping */}
            {preview.unknown_employee_roles.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-foreground">{t('page.user_import.unknown_employee_roles')}</h3>
                {preview.unknown_employee_roles.map((role) => {
                  const mapping = roleMapping[role] ?? { action: 'create' as const };
                  return (
                    <div key={role} className="rounded-lg border border-border p-3 space-y-2">
                      <p className="text-sm font-medium text-foreground">{role}</p>
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                        <select
                          value={mapping.action}
                          onChange={(e) => {
                            const action = e.target.value as 'create' | 'map';
                            setRoleMapping((prev) => ({
                              ...prev,
                              [role]: action === 'create' ? { action: 'create' } : { action: 'map', employee_role_id: '' },
                            }));
                          }}
                          className="w-full sm:w-auto bg-card text-sm"
                        >
                          <option value="create">{t('page.user_import.role_action_create')}</option>
                          <option value="map">{t('page.user_import.role_action_map')}</option>
                        </select>
                        {mapping.action === 'map' && (
                          <select
                            value={mapping.employee_role_id}
                            onChange={(e) => {
                              setRoleMapping((prev) => ({
                                ...prev,
                                [role]: { action: 'map', employee_role_id: e.target.value },
                              }));
                            }}
                            className="w-full sm:flex-1 bg-card text-sm"
                          >
                            <option value="">{t('page.user_import.select_employee_role')}</option>
                            {existingEmployeeRoles.map((r) => (
                              <option key={r.id} value={r.id}>{r.name}</option>
                            ))}
                          </select>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Confirm error */}
            {confirmMutation.isError && (
              <div className="bg-destructive/15 border border-destructive/20 rounded p-3">
                <p className="text-sm text-destructive">
                  {(confirmMutation.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.user_import.error_confirm')}
                </p>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3">
              <button
                type="button"
                disabled={!allDeptsResolved || !allRolesResolved || confirmMutation.isPending || preview.valid_rows === 0}
                onClick={() => confirmMutation.mutate()}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
              >
                {confirmMutation.isPending ? t('page.user_import.confirming') : t('page.user_import.confirm')}
              </button>
              <button
                type="button"
                disabled={confirmMutation.isPending}
                onClick={() => {
                  setStep('upload');
                  setPreview(null);
                  setDeptMapping({});
                  setRoleMapping({});
                  setFile(null);
                  previewMutation.reset();
                }}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
              >
                {t('common.cancel')}
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: Result */}
        {step === 'result' && result && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-foreground">{t('page.user_import.result_title')}</h3>

            <p className="text-sm text-success">{t('page.user_import.successful', { count: result.successful })}</p>
            {result.updated > 0 && (
              <p className="text-sm text-foreground">{t('page.user_import.updated', { count: result.updated })}</p>
            )}
            <p className="text-sm text-muted-foreground">{t('page.user_import.invitations_sent', { count: result.invitations_sent })}</p>

            {result.departments_created.length > 0 && (
              <div>
                <p className="text-sm font-medium text-foreground mb-1">{t('page.user_import.departments_created')}</p>
                <ul className="text-sm text-muted-foreground list-disc pl-4">
                  {result.departments_created.map((d, i) => <li key={i}>{d}</li>)}
                </ul>
              </div>
            )}

            {result.employee_roles_created.length > 0 && (
              <div>
                <p className="text-sm font-medium text-foreground mb-1">{t('page.user_import.employee_roles_created')}</p>
                <ul className="text-sm text-muted-foreground list-disc pl-4">
                  {result.employee_roles_created.map((r, i) => <li key={i}>{r}</li>)}
                </ul>
              </div>
            )}

            {result.failed.length > 0 && (
              <div className="bg-destructive/15 border border-destructive/20 rounded p-3">
                <p className="text-sm font-medium text-destructive mb-2">
                  {t('page.user_import.failed_rows')} ({t('page.user_import.errors_count', { count: result.failed.length })})
                </p>
                <ul className="text-xs text-destructive list-disc pl-4 space-y-0.5">
                  {result.failed.map((e, i) => (
                    <li key={i}>
                      <span className="font-medium">{t('page.user_import.row_n', { row: e.row })}</span>: {e.error}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <button
              type="button"
              onClick={() => navigate('/users')}
              className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
            >
              {t('page.user_import.back_to_users')}
            </button>
          </div>
        )}
      </Card>
    </div>
  );
}
