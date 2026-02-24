import type { CustomFieldDefinition } from '../../../types';

interface Props {
  definition: CustomFieldDefinition;
  value: unknown;
  onChange: (value: unknown) => void;
}

export function NumberField({ definition, value, onChange }: Props) {
  return (
    <div>
      <label className="mb-1.5 block text-sm text-muted-foreground">
        {definition.label}
        {definition.required && <span className="text-destructive"> *</span>}
      </label>
      <input
        type="number"
        step="any"
        value={value != null ? String(value) : ''}
        onChange={(e) => {
          const v = e.target.value;
          onChange(v === '' ? null : Number(v));
        }}
        className="w-full bg-card"
        required={definition.required}
      />
      {definition.description && (
        <p className="mt-1 text-xs text-muted-foreground">{definition.description}</p>
      )}
    </div>
  );
}
