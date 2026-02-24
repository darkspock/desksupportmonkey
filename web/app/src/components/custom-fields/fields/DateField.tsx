import type { CustomFieldDefinition } from '../../../types';

interface Props {
  definition: CustomFieldDefinition;
  value: unknown;
  onChange: (value: unknown) => void;
}

export function DateField({ definition, value, onChange }: Props) {
  return (
    <div>
      <label className="mb-1.5 block text-sm text-muted-foreground">
        {definition.label}
        {definition.required && <span className="text-destructive"> *</span>}
      </label>
      <input
        type="date"
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
