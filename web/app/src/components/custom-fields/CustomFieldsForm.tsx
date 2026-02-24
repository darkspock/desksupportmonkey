import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { useI18n } from '../../lib/i18n';
import type { CustomFieldDefinition } from '../../types';
import { TextField } from './fields/TextField';
import { NumberField } from './fields/NumberField';
import { DateField } from './fields/DateField';
import { SelectField } from './fields/SelectField';
import { MultiSelectField } from './fields/MultiSelectField';
import { BooleanField } from './fields/BooleanField';
import { FileField } from './fields/FileField';

interface CustomFieldsFormProps {
  entityType: 'asset' | 'request' | 'incident';
  values: Record<string, unknown>;
  onChange: (data: Record<string, unknown>) => void;
  isEmployee?: boolean;
}

export function CustomFieldsForm({ entityType, values, onChange, isEmployee }: CustomFieldsFormProps) {
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

  const filtered = (definitions ?? [])
    .filter((d) => d.is_active)
    .filter((d) => !isEmployee || d.visible_to_employees)
    .sort((a, b) => a.sort_order - b.sort_order);

  if (!filtered.length) return null;

  const handleChange = (key: string, value: unknown) => {
    onChange({ ...values, [key]: value });
  };

  return (
    <div className="space-y-4">
      <hr className="border-border" />
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {filtered.map((def) => {
          const FieldComponent = FIELD_MAP[def.field_type];
          if (!FieldComponent) return null;
          const fullWidth = def.field_type === 'multi_select' || def.field_type === 'file';
          return (
            <div key={def.id} className={fullWidth ? 'md:col-span-2' : undefined}>
              <FieldComponent
                definition={def}
                value={values[def.field_key] ?? null}
                onChange={(v) => handleChange(def.field_key, v)}
                {...(def.field_type === 'file' ? { entityType } : {})}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}

const FIELD_MAP: Record<string, React.ComponentType<{
  definition: CustomFieldDefinition;
  value: unknown;
  onChange: (value: unknown) => void;
}>> = {
  text: TextField,
  number: NumberField,
  date: DateField,
  select: SelectField,
  multi_select: MultiSelectField,
  boolean: BooleanField,
  file: FileField as React.ComponentType<{ definition: CustomFieldDefinition; value: unknown; onChange: (value: unknown) => void }>,
};
