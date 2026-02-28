import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import api from '../../lib/api';
import { useI18n } from '../../lib/i18n';
import { useToast } from '../../hooks/useToast';
import { useAuth } from '../../contexts/AuthContext';
import { Loading } from '../../components/ui/Loading';
import {
  MODULES,
  SECTORS,
  SECTOR_FRAMEWORKS,
  FRAMEWORKS,
  type ModuleDefinition,
} from '../../config/moduleConfig';

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

const FRAMEWORK_COLORS: Record<string, string> = {
  blue: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  purple: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
  green: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  amber: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300',
};

const MODULE_ICONS: Record<string, string> = {
  service_desk: 'M8.625 9.75a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375m-13.5 3.01c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.184-4.183a1.14 1.14 0 0 1 .778-.332 48.294 48.294 0 0 0 5.83-.498c1.585-.233 2.708-1.626 2.708-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0 0 12 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018Z',
  asset_inventory: 'M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375',
  procurement: 'M2.25 3h1.386c.51 0 .955.343 1.087.835l.383 1.437M7.5 14.25a3 3 0 0 0-3 3h15.75m-12.75-3h11.218c1.121-2.3 2.1-4.684 2.924-7.138a60.114 60.114 0 0 0-16.536-1.84M7.5 14.25 5.106 5.272M6 20.25a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0Zm12.75 0a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0Z',
  knowledge_base: 'M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25',
  compliance_audit: 'M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z',
  security: 'M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z',
  change_management: 'M7.5 21 3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5',
  maintenance: 'M11.42 15.17 17.25 21A2.652 2.652 0 0 0 21 17.25l-5.877-5.877M11.42 15.17l2.496-3.03c.317-.384.74-.626 1.208-.766M11.42 15.17l-4.655 5.653a2.548 2.548 0 1 1-3.586-3.586l6.837-5.63m5.108-.233c.55-.164 1.163-.188 1.743-.14a4.5 4.5 0 0 0 4.486-6.336l-3.276 3.277a3.004 3.004 0 0 1-2.25-2.25l3.276-3.276a4.5 4.5 0 0 0-6.336 4.486c.091 1.076-.071 2.264-.904 2.95l-.102.085',
  logistics: 'M8.25 18.75a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m3 0h6m-9 0H3.375a1.125 1.125 0 0 1-1.125-1.125V14.25m17.25 4.5a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m3 0h1.125c.621 0 1.129-.504 1.09-1.124a17.902 17.902 0 0 0-3.213-9.193 2.056 2.056 0 0 0-1.58-.86H14.25M16.5 18.75h-2.25m0-11.177v-.958c0-.568-.422-1.048-.987-1.106a48.554 48.554 0 0 0-10.026 0 1.106 1.106 0 0 0-.987 1.106v7.635m12-6.677v6.677m0 4.5v-4.5m0 0h-12',
};

const SECTOR_ICONS: Record<string, string> = {
  financial_services: 'M2.25 18.75a60.07 60.07 0 0 1 15.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 0 1 3 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 0 0-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 0 1-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 0 0 3 15h-.75M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm3 0h.008v.008H18V10.5Zm-12 0h.008v.008H6V10.5Z',
  healthcare: 'M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12Z',
  government: 'M12 21v-8.25M15.75 21v-8.25M8.25 21v-8.25M3 9l9-6 9 6m-1.5 12V10.332A48.36 48.36 0 0 0 12 9.75c-2.551 0-5.056.2-7.5.582V21M3 21h18M12 6.75h.008v.008H12V6.75Z',
  education: 'M4.26 10.147a60.438 60.438 0 0 0-.491 6.347A48.62 48.62 0 0 1 12 20.904a48.62 48.62 0 0 1 8.232-4.41 60.46 60.46 0 0 0-.491-6.347m-15.482 0a50.636 50.636 0 0 0-2.658-.813A59.906 59.906 0 0 1 12 3.493a59.903 59.903 0 0 1 10.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.717 50.717 0 0 1 12 13.489a50.702 50.702 0 0 1 7.74-3.342M6.75 15a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm0 0v-3.675A55.378 55.378 0 0 1 12 8.443m-7.007 11.55A5.981 5.981 0 0 0 6.75 15.75v-1.5',
  technology: 'M9 17.25v1.007a3 3 0 0 1-.879 2.122L7.5 21h9l-.621-.621A3 3 0 0 1 15 18.257V17.25m6-12V15a2.25 2.25 0 0 1-2.25 2.25H5.25A2.25 2.25 0 0 1 3 15V5.25m18 0A2.25 2.25 0 0 0 18.75 3H5.25A2.25 2.25 0 0 0 3 5.25m18 0V12a2.25 2.25 0 0 1-2.25 2.25H5.25A2.25 2.25 0 0 1 3 12V5.25',
  manufacturing: 'M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.277-4.216.42-6.378.42s-4.291-.143-6.378-.42c-1.085-.144-1.872-1.086-1.872-2.18v-4.25m16.5 0a2.18 2.18 0 0 0 .75-1.661V8.706c0-1.081-.768-2.015-1.837-2.175a48.114 48.114 0 0 0-3.413-.387m4.5 8.006c-.194.165-.42.295-.673.38A23.978 23.978 0 0 1 12 15.75c-2.648 0-5.195-.429-7.577-1.22a2.016 2.016 0 0 1-.673-.38m0 0A2.18 2.18 0 0 1 3 12.489V8.706c0-1.081.768-2.015 1.837-2.175a48.111 48.111 0 0 1 3.413-.387m7.5 0V5.25A2.25 2.25 0 0 0 13.5 3h-3a2.25 2.25 0 0 0-2.25 2.25v.894m7.5 0a48.667 48.667 0 0 0-7.5 0',
  retail: 'M15.75 10.5V6a3.75 3.75 0 1 0-7.5 0v4.5m11.356-1.993 1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 0 1-1.12-1.243l1.264-12A1.125 1.125 0 0 1 5.513 7.5h12.974c.576 0 1.059.435 1.119 1.007ZM8.625 10.5a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm7.5 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z',
  energy: 'm3.75 13.5 10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75Z',
  telecommunications: 'M8.288 15.038a5.25 5.25 0 0 1 7.424 0M5.106 11.856c3.807-3.808 9.98-3.808 13.788 0M1.924 8.674c5.565-5.565 14.587-5.565 20.152 0M12.53 18.22l-.53.53-.53-.53a.75.75 0 0 1 1.06 0Z',
  professional_services: 'M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.277-4.216.42-6.378.42s-4.291-.143-6.378-.42c-1.085-.144-1.872-1.086-1.872-2.18v-4.25m16.5 0a2.18 2.18 0 0 0 .75-1.661V8.706c0-1.081-.768-2.015-1.837-2.175a48.114 48.114 0 0 0-3.413-.387m4.5 8.006c-.194.165-.42.295-.673.38A23.978 23.978 0 0 1 12 15.75c-2.648 0-5.195-.429-7.577-1.22a2.016 2.016 0 0 1-.673-.38m0 0A2.18 2.18 0 0 1 3 12.489V8.706c0-1.081.768-2.015 1.837-2.175a48.111 48.111 0 0 1 3.413-.387m7.5 0V5.25A2.25 2.25 0 0 0 13.5 3h-3a2.25 2.25 0 0 0-2.25 2.25v.894m7.5 0a48.667 48.667 0 0 0-7.5 0',
  logistics: 'M8.25 18.75a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m3 0h6m-9 0H3.375a1.125 1.125 0 0 1-1.125-1.125V14.25m17.25 4.5a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m3 0h1.125c.621 0 1.129-.504 1.09-1.124a17.902 17.902 0 0 0-3.213-9.193 2.056 2.056 0 0 0-1.58-.86H14.25M16.5 18.75h-2.25m0-11.177v-.958c0-.568-.422-1.048-.987-1.106a48.554 48.554 0 0 0-10.026 0 1.106 1.106 0 0 0-.987 1.106v7.635m12-6.677v6.677m0 4.5v-4.5m0 0h-12',
  other: 'M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z',
};

const TOTAL_STEPS = 4;

export default function OnboardingWizardPage() {
  const { t } = useI18n();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const { refreshUser } = useAuth();
  const [params] = useSearchParams();
  const isRerun = params.get('rerun') === 'true';

  const [step, setStep] = useState(1);
  const [selectedSector, setSelectedSector] = useState<string | null>(null);
  const [selectedFrameworks, setSelectedFrameworks] = useState<string[]>([]);
  const [selectedModules, setSelectedModules] = useState<string[]>(
    MODULES.filter((m) => m.always_on).map((m) => m.id),
  );
  const [submitting, setSubmitting] = useState(false);
  const [loadingPrefill, setLoadingPrefill] = useState(isRerun);

  // Pre-fill for rerun
  useEffect(() => {
    if (!isRerun) return;
    (async () => {
      try {
        const [settingsRes, controlsRes, navRes] = await Promise.all([
          api.get('/my/company-settings'),
          api.get('/audit/controls').catch(() => ({ data: { data: [] } })),
          api.get('/settings/nav-visibility').catch(() => ({ data: { data: null } })),
        ]);
        const sector = settingsRes.data.data?.sector;
        if (sector) setSelectedSector(sector);

        const controls = controlsRes.data.data as Array<{ framework: string }>;
        const activeFrameworks = [...new Set(controls.map((c) => c.framework))];
        if (activeFrameworks.length) setSelectedFrameworks(activeFrameworks);

        const hiddenItems = navRes.data.data?.hidden_nav_items as Record<string, string[]> | null;
        if (hiddenItems) {
          const hiddenPaths = new Set(Object.values(hiddenItems).flat());
          const active = MODULES.filter((m) => {
            if (m.always_on) return true;
            return !m.navPaths.every((p) => hiddenPaths.has(p));
          }).map((m) => m.id);
          setSelectedModules(active);
        } else {
          setSelectedModules(MODULES.map((m) => m.id));
        }
      } catch {
        // ignore prefill errors
      } finally {
        setLoadingPrefill(false);
      }
    })();
  }, [isRerun]);

  // Update recommended frameworks when sector changes
  const handleSectorSelect = useCallback((sectorId: string) => {
    setSelectedSector(sectorId);
    const recommended = SECTOR_FRAMEWORKS[sectorId] || [];
    setSelectedFrameworks(recommended);
  }, []);

  const toggleFramework = (key: string) => {
    setSelectedFrameworks((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key],
    );
  };

  const toggleModule = (id: string) => {
    const mod = MODULES.find((m) => m.id === id);
    if (mod?.always_on) return;
    setSelectedModules((prev) =>
      prev.includes(id) ? prev.filter((m) => m !== id) : [...prev, id],
    );
  };

  const handleSkip = async () => {
    setSubmitting(true);
    try {
      await api.post('/my/onboarding/complete', { sector: null });
      await refreshUser();
      navigate('/dashboard', { replace: true });
    } catch {
      showToast({ title: t('onboarding.error'), variant: 'error' });
      navigate('/dashboard', { replace: true });
    } finally {
      setSubmitting(false);
    }
  };

  const handleFinish = async () => {
    setSubmitting(true);
    try {
      // 1. Save sector + mark onboarding complete
      await api.post('/my/onboarding/complete', { sector: selectedSector });

      // 2. Seed compliance frameworks
      for (const fw of selectedFrameworks) {
        const seeds = PREDEFINED_CONTROLS[fw] || [];
        for (const seed of seeds) {
          try {
            await api.post('/audit/controls', {
              code: seed.code,
              name: seed.name,
              framework: fw,
              description: null,
            });
          } catch {
            // ignore 409 duplicates
          }
        }
      }

      // 3. Build hidden_nav_items from deselected modules
      const deselectedModules = MODULES.filter(
        (m) => !m.always_on && !selectedModules.includes(m.id),
      );
      const hiddenPaths = deselectedModules.flatMap((m) => m.navPaths);

      if (hiddenPaths.length > 0) {
        const roles = ['admin', 'employee', 'technician', 'procurement_manager'];
        const hiddenNavItems: Record<string, string[]> = {};
        for (const role of roles) {
          hiddenNavItems[role] = hiddenPaths;
        }
        try {
          await api.put('/settings/nav-visibility', { hidden_nav_items: hiddenNavItems });
        } catch {
          // non-fatal
        }
      }

      // 4. Refresh user data (AuthContext, not React Query)
      await refreshUser();

      showToast({ title: t('onboarding.success'), variant: 'success' });
      navigate('/dashboard', { replace: true });
    } catch {
      showToast({ title: t('onboarding.error'), variant: 'error' });
      navigate('/dashboard', { replace: true });
    } finally {
      setSubmitting(false);
    }
  };

  if (loadingPrefill) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-white dark:bg-gray-950">
        <Loading />
      </div>
    );
  }

  const recommendedFrameworks = selectedSector ? (SECTOR_FRAMEWORKS[selectedSector] || []) : [];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-white dark:bg-gray-950">
      <div className="mx-auto flex min-h-full max-w-2xl flex-col px-4 py-8 sm:py-12">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white sm:text-3xl">
            {t('onboarding.title')}
          </h1>
          <p className="mt-2 text-gray-500 dark:text-gray-400">
            {t('onboarding.subtitle')}
          </p>
        </div>

        {/* Progress */}
        <div className="mb-8">
          <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400 mb-2">
            <span>{t('onboarding.step_of', { current: String(step), total: String(TOTAL_STEPS) })}</span>
            <button
              type="button"
              onClick={handleSkip}
              disabled={submitting}
              className="text-sm text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            >
              {t('onboarding.skip')}
            </button>
          </div>
          <div className="h-2 rounded-full bg-gray-100 dark:bg-gray-800">
            <div
              className="h-2 rounded-full bg-primary transition-all duration-300"
              style={{ width: `${(step / TOTAL_STEPS) * 100}%` }}
            />
          </div>
        </div>

        {/* Step content */}
        <div className="flex-1">
          {step === 1 && (
            <SectorStep
              selected={selectedSector}
              onSelect={handleSectorSelect}
              t={t}
            />
          )}
          {step === 2 && (
            <FrameworkStep
              selected={selectedFrameworks}
              recommended={recommendedFrameworks}
              onToggle={toggleFramework}
              t={t}
            />
          )}
          {step === 3 && (
            <ModuleStep
              selected={selectedModules}
              onToggle={toggleModule}
              t={t}
            />
          )}
          {step === 4 && (
            <SummaryStep
              sector={selectedSector}
              frameworks={selectedFrameworks}
              modules={selectedModules}
              t={t}
            />
          )}
        </div>

        {/* Navigation */}
        <div className="mt-8 flex items-center justify-between border-t border-gray-100 dark:border-gray-800 pt-6">
          <div>
            {step > 1 && (
              <button
                type="button"
                onClick={() => setStep((s) => s - 1)}
                disabled={submitting}
                className="inline-flex items-center gap-1 rounded-md px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              >
                <svg viewBox="0 0 20 20" className="h-4 w-4" fill="currentColor">
                  <path fillRule="evenodd" d="M17 10a.75.75 0 0 1-.75.75H5.612l4.158 3.96a.75.75 0 1 1-1.04 1.08l-5.5-5.25a.75.75 0 0 1 0-1.08l5.5-5.25a.75.75 0 1 1 1.04 1.08L5.612 9.25H16.25A.75.75 0 0 1 17 10Z" clipRule="evenodd" />
                </svg>
                {t('onboarding.back')}
              </button>
            )}
          </div>
          <div>
            {step < TOTAL_STEPS ? (
              <button
                type="button"
                onClick={() => setStep((s) => s + 1)}
                className="inline-flex items-center gap-1 rounded-md bg-primary px-5 py-2 text-sm font-medium text-primary-foreground shadow-xs hover:bg-primary/90 transition-colors"
              >
                {t('onboarding.next')}
                <svg viewBox="0 0 20 20" className="h-4 w-4" fill="currentColor">
                  <path fillRule="evenodd" d="M3 10a.75.75 0 0 1 .75-.75h10.638L10.23 5.29a.75.75 0 1 1 1.04-1.08l5.5 5.25a.75.75 0 0 1 0 1.08l-5.5 5.25a.75.75 0 1 1-1.04-1.08l4.158-3.96H3.75A.75.75 0 0 1 3 10Z" clipRule="evenodd" />
                </svg>
              </button>
            ) : (
              <button
                type="button"
                onClick={handleFinish}
                disabled={submitting}
                className="inline-flex items-center gap-2 rounded-md bg-primary px-5 py-2 text-sm font-medium text-primary-foreground shadow-xs hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                {submitting ? (
                  <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" className="opacity-25" />
                    <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" className="opacity-75" />
                  </svg>
                ) : null}
                {t('onboarding.finish')}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function SectorStep({
  selected,
  onSelect,
  t,
}: {
  selected: string | null;
  onSelect: (id: string) => void;
  t: (key: string) => string;
}) {
  return (
    <div>
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
        {t('onboarding.sector.title')}
      </h2>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
        {t('onboarding.sector.subtitle')}
      </p>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {SECTORS.map((sector) => {
          const isSelected = selected === sector.id;
          const icon = SECTOR_ICONS[sector.id] || SECTOR_ICONS.other;
          return (
            <button
              key={sector.id}
              type="button"
              onClick={() => onSelect(sector.id)}
              className={`flex flex-col items-center gap-2 rounded-xl border-2 p-4 text-center transition-all ${
                isSelected
                  ? 'border-primary bg-primary/5 dark:bg-primary/10'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
              }`}
            >
              <svg viewBox="0 0 24 24" className={`h-6 w-6 ${isSelected ? 'text-primary' : 'text-gray-400 dark:text-gray-500'}`} fill="none" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d={icon} />
              </svg>
              <span className={`text-sm font-medium ${isSelected ? 'text-primary' : 'text-gray-700 dark:text-gray-300'}`}>
                {t(sector.labelKey)}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function FrameworkStep({
  selected,
  recommended,
  onToggle,
  t,
}: {
  selected: string[];
  recommended: string[];
  onToggle: (key: string) => void;
  t: (key: string) => string;
}) {
  return (
    <div>
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
        {t('onboarding.frameworks.title')}
      </h2>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
        {t('onboarding.frameworks.subtitle')}
      </p>
      <div className="space-y-3">
        {FRAMEWORKS.map((fw) => {
          const isChecked = selected.includes(fw.key);
          const isRecommended = recommended.includes(fw.key);
          const colorClass = FRAMEWORK_COLORS[fw.color] || FRAMEWORK_COLORS.blue;
          return (
            <label
              key={fw.key}
              className={`flex items-center gap-4 rounded-xl border-2 p-4 cursor-pointer transition-all ${
                isChecked
                  ? 'border-primary bg-primary/5 dark:bg-primary/10'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
              }`}
            >
              <input
                type="checkbox"
                checked={isChecked}
                onChange={() => onToggle(fw.key)}
                className="h-5 w-5 rounded border-gray-300 text-primary focus:ring-primary"
              />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-900 dark:text-white">{fw.name}</span>
                  {isRecommended && (
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${colorClass}`}>
                      {t('onboarding.frameworks.recommended')}
                    </span>
                  )}
                </div>
              </div>
            </label>
          );
        })}
      </div>
    </div>
  );
}

function ModuleStep({
  selected,
  onToggle,
  t,
}: {
  selected: string[];
  onToggle: (id: string) => void;
  t: (key: string) => string;
}) {
  return (
    <div>
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
        {t('onboarding.modules.title')}
      </h2>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
        {t('onboarding.modules.subtitle')}
      </p>
      <div className="space-y-3">
        {MODULES.map((mod: ModuleDefinition) => {
          const isActive = selected.includes(mod.id);
          const icon = MODULE_ICONS[mod.id] || MODULE_ICONS.service_desk;
          return (
            <button
              key={mod.id}
              type="button"
              onClick={() => toggleModule(mod, onToggle)}
              disabled={mod.always_on}
              className={`flex w-full items-center gap-4 rounded-xl border-2 p-4 text-left transition-all ${
                mod.always_on
                  ? 'border-green-200 bg-green-50/50 dark:border-green-800 dark:bg-green-900/10 cursor-default'
                  : isActive
                    ? 'border-primary bg-primary/5 dark:bg-primary/10 cursor-pointer'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 cursor-pointer'
              }`}
            >
              <svg viewBox="0 0 24 24" className={`h-6 w-6 flex-shrink-0 ${isActive || mod.always_on ? 'text-primary' : 'text-gray-400'}`} fill="none" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d={icon} />
              </svg>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={`font-medium ${isActive || mod.always_on ? 'text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400'}`}>
                    {t(mod.labelKey)}
                  </span>
                  {mod.always_on && (
                    <span className="inline-flex items-center rounded-full bg-green-100 dark:bg-green-900/30 px-2 py-0.5 text-xs font-medium text-green-700 dark:text-green-300">
                      {t('onboarding.modules.always_on')}
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                  {t(mod.descriptionKey)}
                </p>
              </div>
              {!mod.always_on && (
                <div className={`relative inline-flex h-6 w-11 shrink-0 rounded-full border-2 border-transparent transition-colors duration-200 ${
                  isActive ? 'bg-primary' : 'bg-gray-300 dark:bg-gray-600'
                }`}>
                  <span className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow-sm transition-transform duration-200 ${
                    isActive ? 'translate-x-5' : 'translate-x-0'
                  }`} />
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function toggleModule(mod: ModuleDefinition, onToggle: (id: string) => void) {
  if (mod.always_on) return;
  onToggle(mod.id);
}

function SummaryStep({
  sector,
  frameworks,
  modules,
  t,
}: {
  sector: string | null;
  frameworks: string[];
  modules: string[];
  t: (key: string) => string;
}) {
  const sectorDef = SECTORS.find((s) => s.id === sector);
  const activeModules = MODULES.filter((m) => modules.includes(m.id));

  return (
    <div>
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
        {t('onboarding.summary.title')}
      </h2>
      <div className="space-y-6">
        {/* Sector */}
        <div className="rounded-xl border border-gray-200 dark:border-gray-700 p-4">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
            {t('onboarding.summary.sector')}
          </h3>
          <p className="font-medium text-gray-900 dark:text-white">
            {sectorDef ? t(sectorDef.labelKey) : t('onboarding.summary.none_selected')}
          </p>
        </div>

        {/* Frameworks */}
        <div className="rounded-xl border border-gray-200 dark:border-gray-700 p-4">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
            {t('onboarding.summary.frameworks')}
          </h3>
          {frameworks.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {frameworks.map((fw) => {
                const fwDef = FRAMEWORKS.find((f) => f.key === fw);
                const colorClass = fwDef ? (FRAMEWORK_COLORS[fwDef.color] || FRAMEWORK_COLORS.blue) : FRAMEWORK_COLORS.blue;
                return (
                  <span key={fw} className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-medium ${colorClass}`}>
                    {fw}
                  </span>
                );
              })}
            </div>
          ) : (
            <p className="text-gray-400 dark:text-gray-500">{t('onboarding.summary.none_selected')}</p>
          )}
        </div>

        {/* Modules */}
        <div className="rounded-xl border border-gray-200 dark:border-gray-700 p-4">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
            {t('onboarding.summary.modules')}
          </h3>
          <div className="flex flex-wrap gap-2">
            {activeModules.map((mod) => (
              <span key={mod.id} className="inline-flex items-center rounded-full bg-gray-100 dark:bg-gray-800 px-3 py-1 text-sm font-medium text-gray-700 dark:text-gray-300">
                {t(mod.labelKey)}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
