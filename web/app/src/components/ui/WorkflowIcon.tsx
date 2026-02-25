import { icons, type LucideProps } from 'lucide-react';

interface WorkflowIconProps extends Omit<LucideProps, 'name'> {
  name?: string | null;
}

/**
 * Renders a lucide-react icon by its kebab-case name (e.g. "alert-circle").
 * Returns null for unknown or missing names.
 */
export function WorkflowIcon({ name, ...props }: WorkflowIconProps) {
  if (!name) return null;
  const pascalName = name.replace(/(^|-)(\w)/g, (_, __, c: string) => c.toUpperCase());
  const Icon = icons[pascalName as keyof typeof icons];
  if (!Icon) return null;
  return <Icon {...props} />;
}
