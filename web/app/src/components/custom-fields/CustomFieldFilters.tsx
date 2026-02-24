import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { useI18n } from '../../lib/i18n';
import type { CustomFieldDefinition } from '../../types';

interface CustomFieldFiltersProps {
  entityType: 'asset' | 'request' | 'incident';
  filters: Record<string, string>;
  onFilterChange: (key: string, value: string) => void;
}

export function CustomFieldFilters({ entityType, filters, onFilterChange }: CustomFieldFiltersProps) {
  const { t } = useI18n();

  const { data: definitions } = useQuery({
    queryKey: ['cf-definitions', entityType],
    queryFn: async () => {
      const { data } = await api.get('/custom-fields/definitions', {
        params: { entity_type: entityType },
      });
      return data.data as CustomFieldDefinition[];
    },
  });

  const filterable = (definitions ?? [])
    .filter((d) => d.is_active && ['select', 'boolean'].includes(d.field_type))
    .sort((a, b) => a.sort_order - b.sort_order);

  if (!filterable.length) return null;

  return (
    <>
      {filterable.map((def) => (
        <select
          key={def.field_key}
          value={filters[`cf_${def.field_key}`] ?? ''}
          onChange={(e) => onFilterChange(`cf_${def.field_key}`, e.target.value)}
          className="w-[180px] bg-card"
        >
          <option value="">{def.label}</option>
          {def.field_type === 'boolean' ? (
            <>
              <option value="true">{t('page.custom_fields.yes')}</option>
              <option value="false">{t('page.custom_fields.no')}</option>
            </>
          ) : (
            (def.options ?? []).map((opt) => (
              <option key={opt} value={opt}>{opt}</option>
            ))
          )}
        </select>
      ))}
    </>
  );
}
