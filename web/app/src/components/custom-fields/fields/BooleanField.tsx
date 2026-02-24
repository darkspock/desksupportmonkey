import type { CustomFieldDefinition } from '../../../types';

interface Props {
  definition: CustomFieldDefinition;
  value: unknown;
  onChange: (value: unknown) => void;
}

export function BooleanField({ definition, value, onChange }: Props) {
  return (
    <div>
      <label className="inline-flex cursor-pointer items-center gap-2 text-sm text-foreground">
        <input
          type="checkbox"
          checked={value === true}
          onChange={(e) => onChange(e.target.checked)}
          className="h-4 w-4 rounded border-border"
        />
        <span>
          {definition.label}
          {definition.required && <span className="text-destructive"> *</span>}
        </span>
      </label>
      {definition.description && (
        <p className="mt-1 text-xs text-muted-foreground">{definition.description}</p>
      )}
    </div>
  );
}
