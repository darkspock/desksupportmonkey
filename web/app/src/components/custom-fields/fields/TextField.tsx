import type { CustomFieldDefinition } from '../../../types';
import { useI18n } from '../../../lib/i18n';

interface Props {
  definition: CustomFieldDefinition;
  value: unknown;
  onChange: (value: unknown) => void;
}

export function TextField({ definition, value, onChange }: Props) {
  const { t } = useI18n();
  return (
    <div>
      <label className="mb-1.5 block text-sm text-muted-foreground">
        {definition.label}
        {definition.required && <span className="text-destructive"> *</span>}
      </label>
      <input
        type="text"
        value={(value as string) ?? ''}
        onChange={(e) => onChange(e.target.value || null)}
        className="w-full bg-card"
        required={definition.required}
      />
      {definition.description && (
        <p className="mt-1 text-xs text-muted-foreground">{definition.description}</p>
      )}
    </div>
  );
}
