import type { CustomFieldDefinition } from '../../../types';
import { useI18n } from '../../../lib/i18n';

interface Props {
  definition: CustomFieldDefinition;
  value: unknown;
  onChange: (value: unknown) => void;
}

export function MultiSelectField({ definition, value, onChange }: Props) {
  const { t } = useI18n();
  const selected = Array.isArray(value) ? (value as string[]) : [];

  const toggle = (opt: string) => {
    const next = selected.includes(opt)
      ? selected.filter((s) => s !== opt)
      : [...selected, opt];
    onChange(next.length ? next : null);
  };

  return (
    <div>
      <label className="mb-1.5 block text-sm text-muted-foreground">
        {definition.label}
        {definition.required && <span className="text-destructive"> *</span>}
      </label>
      <p className="mb-2 text-xs text-muted-foreground">{t('page.custom_fields.multi_select_hint')}</p>
      <div className="flex flex-wrap gap-2">
        {(definition.options ?? []).map((opt) => {
          const checked = selected.includes(opt);
          return (
            <label
              key={opt}
              className={`inline-flex cursor-pointer items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm transition-colors ${
                checked
                  ? 'border-primary bg-primary/10 text-primary'
                  : 'border-border bg-card text-foreground hover:bg-accent'
              }`}
            >
              <input
                type="checkbox"
                checked={checked}
                onChange={() => toggle(opt)}
                className="sr-only"
              />
              {opt}
            </label>
          );
        })}
      </div>
      {definition.description && (
        <p className="mt-1 text-xs text-muted-foreground">{definition.description}</p>
      )}
    </div>
  );
}
