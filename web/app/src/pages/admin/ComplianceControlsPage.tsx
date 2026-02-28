import { Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { ErrorState } from '../../components/ui/StateBlock';
import { useI18n } from '../../lib/i18n';
import { useToast } from '../../components/ui/Toast';
import type { ComplianceControl } from '../../types';

interface FrameworkInfo {
  key: string;
  name: string;
  color: string;
  iconPath: string;
}

const FRAMEWORKS: FrameworkInfo[] = [
  {
    key: 'NIS2',
    name: 'NIS2',
    color: 'blue',
    iconPath: 'M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z',
  },
  {
    key: 'DORA',
    name: 'DORA',
    color: 'purple',
    iconPath: 'M2.25 18.75a60.07 60.07 0 0 1 15.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 0 1 3 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 0 0-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 0 1-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 0 0 3 15h-.75M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm3 0h.008v.008H18V10.5Zm-12 0h.008v.008H6V10.5Z',
  },
  {
    key: 'ISO 27001',
    name: 'ISO 27001',
    color: 'green',
    iconPath: 'M9 12.75 11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 0 1-1.043 3.296 3.745 3.745 0 0 1-3.296 1.043A3.745 3.745 0 0 1 12 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 0 1-3.296-1.043 3.745 3.745 0 0 1-1.043-3.296A3.745 3.745 0 0 1 3 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 0 1 1.043-3.296 3.746 3.746 0 0 1 3.296-1.043A3.746 3.746 0 0 1 12 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 0 1 3.296 1.043 3.745 3.745 0 0 1 1.043 3.296A3.745 3.745 0 0 1 21 12Z',
  },
  {
    key: 'GDPR',
    name: 'GDPR',
    color: 'amber',
    iconPath: 'M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z',
  },
];

const COLOR_ACTIVE: Record<string, { bg: string; border: string; icon: string }> = {
  blue: {
    bg: 'bg-blue-50 dark:bg-blue-950/30',
    border: 'border-blue-200 dark:border-blue-800',
    icon: 'text-blue-600 dark:text-blue-400',
  },
  purple: {
    bg: 'bg-purple-50 dark:bg-purple-950/30',
    border: 'border-purple-200 dark:border-purple-800',
    icon: 'text-purple-600 dark:text-purple-400',
  },
  green: {
    bg: 'bg-green-50 dark:bg-green-950/30',
    border: 'border-green-200 dark:border-green-800',
    icon: 'text-green-600 dark:text-green-400',
  },
  amber: {
    bg: 'bg-amber-50 dark:bg-amber-950/30',
    border: 'border-amber-200 dark:border-amber-800',
    icon: 'text-amber-600 dark:text-amber-400',
  },
};

const INACTIVE = {
  bg: 'bg-gray-50 dark:bg-gray-800/50',
  border: 'border-gray-200 dark:border-gray-700',
  icon: 'text-gray-400 dark:text-gray-500',
};

// Predefined control seeds per framework (code, name)
const PREDEFINED_CONTROLS: Record<string, Array<{ code: string; name: string }>> = {
  NIS2: [
    { code: 'NIS2-ART21-2A', name: 'Risk analysis and information security policies' },
    { code: 'NIS2-ART21-2B', name: 'Incident handling' },
    { code: 'NIS2-ART21-2E', name: 'Security in network and information systems' },
    { code: 'NIS2-ART21-2I', name: 'Human resources security and access control' },
    { code: 'NIS2-ART21-2J', name: 'Multi-factor authentication' },
  ],
  DORA: [
    { code: 'DORA-CH2-ART5', name: 'ICT risk management framework' },
    { code: 'DORA-CH2-ART9', name: 'Protection and prevention' },
    { code: 'DORA-CH3-ART17', name: 'ICT-related incident management' },
    { code: 'DORA-CH3-ART19', name: 'Reporting of major ICT incidents' },
  ],
  'ISO 27001': [
    { code: 'ISO27001-A5.1', name: 'Policies for information security' },
    { code: 'ISO27001-A5.23', name: 'Information security for use of cloud services' },
    { code: 'ISO27001-A6.1', name: 'Screening' },
    { code: 'ISO27001-A8.2', name: 'Privileged access rights' },
    { code: 'ISO27001-A8.15', name: 'Logging' },
    { code: 'ISO27001-A8.16', name: 'Monitoring activities' },
  ],
  GDPR: [
    { code: 'GDPR-ART5', name: 'Principles of data processing' },
    { code: 'GDPR-ART6', name: 'Lawfulness of processing' },
    { code: 'GDPR-ART25', name: 'Data protection by design and by default' },
    { code: 'GDPR-ART30', name: 'Records of processing activities' },
    { code: 'GDPR-ART32', name: 'Security of processing' },
    { code: 'GDPR-ART33', name: 'Notification of personal data breach' },
  ],
};

export default function ComplianceControlsPage() {
  const { t } = useI18n();
  const toast = useToast();
  const queryClient = useQueryClient();

  const { data: controls, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['compliance-controls'],
    queryFn: async () => {
      const { data } = await api.get('/audit/controls');
      return data.data as ComplianceControl[];
    },
  });

  const activateMutation = useMutation({
    mutationFn: async (frameworkKey: string) => {
      const seeds = PREDEFINED_CONTROLS[frameworkKey] || [];
      for (const seed of seeds) {
        try {
          await api.post('/audit/controls', {
            code: seed.code,
            name: seed.name,
            framework: frameworkKey,
            description: null,
          });
        } catch {
          // ignore duplicates (409)
        }
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['compliance-controls'] });
      queryClient.invalidateQueries({ queryKey: ['compliance-dashboard'] });
      toast.success(t('audit.controls.activated'));
    },
    onError: () => toast.error(t('common.error')),
  });

  const deactivateMutation = useMutation({
    mutationFn: async (frameworkKey: string) => {
      const fwControls = (controls || []).filter(
        (c) => c.framework === frameworkKey && !c.is_predefined
      );
      for (const c of fwControls) {
        await api.delete(`/audit/controls/${c.id}`);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['compliance-controls'] });
      queryClient.invalidateQueries({ queryKey: ['compliance-dashboard'] });
      toast.success(t('audit.controls.deactivated_fw'));
    },
    onError: () => toast.error(t('common.error')),
  });

  const controlsByFramework: Record<string, ComplianceControl[]> = {};
  if (controls) {
    for (const c of controls) {
      if (!controlsByFramework[c.framework]) controlsByFramework[c.framework] = [];
      controlsByFramework[c.framework].push(c);
    }
  }

  const isMutating = activateMutation.isPending || deactivateMutation.isPending;

  const handleToggle = (fw: FrameworkInfo) => {
    if (isMutating) return;
    const fwControls = controlsByFramework[fw.key] || [];
    const isActive = fwControls.length > 0;

    if (isActive) {
      const customControls = fwControls.filter((c) => !c.is_predefined);
      const predefinedCount = fwControls.length - customControls.length;
      if (predefinedCount > 0 && customControls.length === 0) {
        toast.info(t('audit.controls.predefined_cannot_deactivate'));
        return;
      }
      if (customControls.length > 0 && confirm(t('audit.controls.confirm_deactivate_fw'))) {
        deactivateMutation.mutate(fw.key);
      }
    } else {
      activateMutation.mutate(fw.key);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t('audit.controls.title')}</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">{t('audit.controls.subtitle')}</p>
      </div>

      {isLoading && <Loading />}
      {isError && <ErrorState message={(error as Error)?.message || t('common.error')} onRetry={refetch} />}

      {controls && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {FRAMEWORKS.map((fw) => {
            const fwControls = controlsByFramework[fw.key] || [];
            const isActive = fwControls.length > 0;
            const colors = isActive ? COLOR_ACTIVE[fw.color] : INACTIVE;

            return (
              <div
                key={fw.key}
                className={`rounded-xl border-2 ${colors.border} ${colors.bg} p-6 flex flex-col gap-4 transition-all`}
              >
                {/* Header: icon + name + toggle */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-lg bg-white dark:bg-gray-800 shadow-sm">
                      <svg viewBox="0 0 24 24" className={`h-6 w-6 ${colors.icon}`} fill="none" stroke="currentColor" strokeWidth="1.5">
                        <path strokeLinecap="round" strokeLinejoin="round" d={fw.iconPath} />
                      </svg>
                    </div>
                    <h3 className={`text-lg font-bold ${isActive ? 'text-gray-900 dark:text-white' : 'text-gray-400 dark:text-gray-500'}`}>
                      {fw.name}
                    </h3>
                  </div>
                  {/* Toggle switch */}
                  <button
                    onClick={() => handleToggle(fw)}
                    disabled={isMutating}
                    className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus:outline-none disabled:opacity-50 ${
                      isActive ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'
                    }`}
                    role="switch"
                    aria-checked={isActive}
                  >
                    <span
                      className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow-sm ring-0 transition-transform duration-200 ${
                        isActive ? 'translate-x-5' : 'translate-x-0'
                      }`}
                    />
                  </button>
                </div>

                {/* Description */}
                <p className={`text-sm leading-relaxed ${isActive ? 'text-gray-600 dark:text-gray-400' : 'text-gray-400 dark:text-gray-500'}`}>
                  {t(`audit.frameworks.${fw.key.replace(/\s/g, '_')}_desc`)}
                </p>

                {/* Footer: controls count + dashboard link */}
                <div className="flex items-center justify-between mt-auto pt-2">
                  <span className={`text-xs ${isActive ? 'text-gray-500 dark:text-gray-400' : 'text-gray-400 dark:text-gray-500'}`}>
                    {isActive
                      ? `${fwControls.length} ${fwControls.length === 1 ? t('audit.controls.control_singular') : t('audit.controls.control_plural')}`
                      : t('audit.controls.inactive_label')
                    }
                  </span>
                  {isActive && (
                    <Link
                      to={`/compliance/dashboard?framework=${encodeURIComponent(fw.key)}`}
                      className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
                    >
                      {t('audit.controls.view_dashboard')}
                      <svg viewBox="0 0 20 20" className="h-3.5 w-3.5" fill="currentColor">
                        <path fillRule="evenodd" d="M3 10a.75.75 0 0 1 .75-.75h10.638L10.23 5.29a.75.75 0 1 1 1.04-1.08l5.5 5.25a.75.75 0 0 1 0 1.08l-5.5 5.25a.75.75 0 1 1-1.04-1.08l4.158-3.96H3.75A.75.75 0 0 1 3 10Z" clipRule="evenodd" />
                      </svg>
                    </Link>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
