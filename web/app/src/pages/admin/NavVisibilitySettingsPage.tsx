import { useState, useEffect, useMemo } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useI18n } from '../../lib/i18n';
import { Loading } from '../../components/ui/Loading';
import { ErrorState } from '../../components/ui/StateBlock';
import api from '../../lib/api';
import { sections, type NavItem, type NavSubGroup } from '../../config/navSections';

interface NavConfigData {
  id: string;
  company_id: string;
  hidden_nav_items: Record<string, string[]>;
}

// Roles that can be configured (super_admin is excluded)
const CONFIGURABLE_ROLES = ['employee', 'technician', 'procurement_manager', 'admin'] as const;
type ConfigurableRole = typeof CONFIGURABLE_ROLES[number];

interface FlatNavItem {
  path: string;
  labelKey: string;
  sectionLabelKey: string;
  subgroupLabelKey?: string;
  roles?: string[]; // hardcoded role access from navSections
}

function flattenNavItems(): FlatNavItem[] {
  const flat: FlatNavItem[] = [];
  for (const section of sections) {
    // Skip platform section (super_admin only)
    if (section.labelKey === 'nav.section_platform') continue;
    for (const entry of section.items) {
      if (entry.type === 'subgroup') {
        const sg = entry as NavSubGroup;
        for (const child of sg.items) {
          flat.push({
            path: child.to,
            labelKey: child.labelKey,
            sectionLabelKey: section.labelKey ?? '',
            subgroupLabelKey: sg.labelKey,
            roles: child.roles,
          });
        }
      } else if (!entry.type) {
        const item = entry as NavItem;
        flat.push({
          path: item.to,
          labelKey: item.labelKey,
          sectionLabelKey: section.labelKey ?? '',
          roles: item.roles,
        });
      }
    }
  }
  return flat;
}

function hasRoleAccess(item: FlatNavItem, role: ConfigurableRole): boolean {
  if (!item.roles) return true; // no role restriction = all roles
  return item.roles.includes(role);
}

export default function NavVisibilitySettingsPage() {
  const { t } = useI18n();
  const flatItems = useMemo(() => flattenNavItems(), []);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['nav-visibility'],
    queryFn: async () => {
      const { data } = await api.get('/settings/nav-visibility');
      return data.data as NavConfigData | null;
    },
  });

  // Local state: set of hidden paths per role
  const [hidden, setHidden] = useState<Record<string, Set<string>>>({
    admin: new Set<string>(),
    employee: new Set<string>(),
    technician: new Set<string>(),
    procurement_manager: new Set<string>(),
  });
  const [isDirty, setIsDirty] = useState(false);

  useEffect(() => {
    if (data) {
      const newHidden: Record<string, Set<string>> = {};
      for (const role of CONFIGURABLE_ROLES) {
        newHidden[role] = new Set(data.hidden_nav_items[role] ?? []);
      }
      setHidden(newHidden);
    }
  }, [data]);

  const mutation = useMutation({
    mutationFn: async (payload: Record<string, string[]>) => {
      const { data } = await api.put('/settings/nav-visibility', {
        hidden_nav_items: payload,
      });
      return data.data;
    },
    onSuccess: () => {
      window.location.reload();
    },
  });

  const toggleItem = (role: ConfigurableRole, path: string) => {
    setHidden((prev) => {
      const roleSet = new Set(prev[role]);
      if (roleSet.has(path)) {
        roleSet.delete(path);
      } else {
        roleSet.add(path);
      }
      return { ...prev, [role]: roleSet };
    });
    setIsDirty(true);
  };

  const handleSave = () => {
    const payload: Record<string, string[]> = {};
    for (const role of CONFIGURABLE_ROLES) {
      const paths = Array.from(hidden[role]);
      if (paths.length > 0) {
        payload[role] = paths;
      }
    }
    mutation.mutate(payload);
  };

  if (isLoading) return <Loading />;
  if (isError) return <ErrorState onRetry={refetch} />;

  // Group items by section for display
  const sectionGroups = new Map<string, FlatNavItem[]>();
  for (const item of flatItems) {
    const key = item.sectionLabelKey;
    if (!sectionGroups.has(key)) sectionGroups.set(key, []);
    sectionGroups.get(key)!.push(item);
  }

  const roleColKey: Record<ConfigurableRole, string> = {
    admin: 'page.nav_visibility.col_admin',
    employee: 'page.nav_visibility.col_employee',
    technician: 'page.nav_visibility.col_technician',
    procurement_manager: 'page.nav_visibility.col_procurement',
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">{t('page.nav_visibility.title')}</h1>
        <p className="text-sm text-muted-foreground mt-1">{t('page.nav_visibility.subtitle')}</p>
      </div>

      <div className="bg-card rounded-lg border shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="text-left px-4 py-3 font-medium">{t('page.nav_visibility.col_item')}</th>
              {CONFIGURABLE_ROLES.map((role) => (
                <th key={role} className="text-center px-4 py-3 font-medium w-32">
                  {t(roleColKey[role])}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from(sectionGroups.entries()).map(([sectionKey, items]) => (
              <>
                <tr key={`section-${sectionKey}`} className="bg-muted/30">
                  <td colSpan={5} className="px-4 py-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    {t(sectionKey)}
                  </td>
                </tr>
                {items.map((item) => (
                  <tr key={item.path} className="border-b last:border-b-0 hover:bg-muted/20">
                    <td className="px-4 py-2.5">
                      <span className="text-foreground">
                        {item.subgroupLabelKey && (
                          <span className="text-muted-foreground text-xs mr-1.5">{t(item.subgroupLabelKey)} /</span>
                        )}
                        {t(item.labelKey)}
                      </span>
                    </td>
                    {CONFIGURABLE_ROLES.map((role) => {
                      const hasAccess = hasRoleAccess(item, role);
                      const isHidden = hidden[role]?.has(item.path);
                      return (
                        <td key={role} className="text-center px-4 py-2.5">
                          {hasAccess ? (
                            <input
                              type="checkbox"
                              checked={!isHidden}
                              onChange={() => toggleItem(role, item.path)}
                              className="h-4 w-4 rounded border-input text-primary focus:ring-primary cursor-pointer"
                            />
                          ) : (
                            <span className="text-xs text-muted-foreground/50" title={t('page.nav_visibility.no_access')}>
                              &mdash;
                            </span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex justify-end gap-3">
        <button
          onClick={handleSave}
          disabled={!isDirty || mutation.isPending}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {mutation.isPending ? t('common.saving') : t('common.save')}
        </button>
      </div>

      {mutation.isSuccess && (
        <p className="text-sm text-green-600">{t('page.nav_visibility.saved')}</p>
      )}
      {mutation.isError && (
        <p className="text-sm text-destructive">{t('page.nav_visibility.error')}</p>
      )}
    </div>
  );
}
