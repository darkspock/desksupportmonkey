import { icons, type LucideProps } from 'lucide-react';

interface WorkflowIconProps extends Omit<LucideProps, 'name'> {
  name?: string | null;
}

/** Map renamed lucide icons so old DB values still resolve. */
const ALIASES: Record<string, string> = {
  AlertCircle: 'CircleAlert',
};

/**
 * Renders a lucide-react icon by its kebab-case name (e.g. "circle-alert").
 * Returns null for unknown or missing names.
 */
export function WorkflowIcon({ name, ...props }: WorkflowIconProps) {
  if (!name) return null;
  const pascalName = name.replace(/(^|-)(\w)/g, (_, __, c: string) => c.toUpperCase());
  const resolved = ALIASES[pascalName] ?? pascalName;
  const Icon = icons[resolved as keyof typeof icons];
  if (!Icon) return null;
  return <Icon {...props} />;
}
