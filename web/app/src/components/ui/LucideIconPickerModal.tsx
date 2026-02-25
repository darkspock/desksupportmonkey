import { useMemo, useState } from 'react';
import { icons, Search, X, type LucideIcon } from 'lucide-react';
import { cn } from '../../lib/cn';
import { useI18n } from '../../lib/i18n';
import { Tooltip } from './Tooltip';

interface LucideIconEntry {
  name: string;
  pascalName: string;
  Icon: LucideIcon;
}

interface LucideIconPickerModalProps {
  open: boolean;
  selectedIcon?: string | null;
  onClose: () => void;
  onSelect: (iconName: string) => void;
}

const MAX_VISIBLE_ICONS = 240;

function pascalToKebab(value: string): string {
  return value
    .replace(/([a-z0-9])([A-Z])/g, '$1-$2')
    .replace(/([A-Z])([A-Z][a-z])/g, '$1-$2')
    .toLowerCase();
}

const ALL_LUCIDE_ICONS: LucideIconEntry[] = Object.entries(icons)
  .map(([pascalName, Icon]) => ({
    name: pascalToKebab(pascalName),
    pascalName,
    Icon: Icon as LucideIcon,
  }))
  .sort((a, b) => a.name.localeCompare(b.name));

export function LucideIconPickerModal({
  open,
  selectedIcon,
  onClose,
  onSelect,
}: LucideIconPickerModalProps) {
  const { t } = useI18n();
  const [query, setQuery] = useState('');

  const handleClose = () => {
    setQuery('');
    onClose();
  };

  const normalizedQuery = query.trim().toLowerCase();

  const { totalMatches, visibleIcons } = useMemo(() => {
    const matches = normalizedQuery
      ? ALL_LUCIDE_ICONS.filter(
          ({ name, pascalName }) =>
            name.includes(normalizedQuery) || pascalName.toLowerCase().includes(normalizedQuery),
        )
      : ALL_LUCIDE_ICONS;

    return {
      totalMatches: matches.length,
      visibleIcons: matches.slice(0, MAX_VISIBLE_ICONS),
    };
  }, [normalizedQuery]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <button
        type="button"
        className="absolute inset-0 bg-black/45"
        onClick={handleClose}
        aria-label={t('errors.close_confirmation_dialog')}
      />

      <div className="relative z-[101] w-full max-w-5xl rounded-xl border border-border bg-card p-6 shadow-lg">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="text-lg font-semibold text-foreground">
              {t('page.workflow_templates.icon_picker_title')}
            </h3>
            <p className="mt-1 text-xs text-muted-foreground">
              {totalMatches > MAX_VISIBLE_ICONS
                ? t('page.workflow_templates.icon_picker_showing_limited', {
                    shown: visibleIcons.length,
                    total: totalMatches,
                  })
                : t('page.workflow_templates.icon_picker_showing_all', {
                    total: totalMatches,
                  })}
            </p>
          </div>

          <button
            type="button"
            onClick={handleClose}
            className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-border bg-background text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            aria-label={t('common.close')}
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="relative mt-4">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t('page.workflow_templates.icon_picker_search_placeholder')}
            className="w-full bg-card pl-9 pr-9"
          />
          {query && (
            <button
              type="button"
              onClick={() => setQuery('')}
              className="absolute right-2 top-1/2 inline-flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
              aria-label={t('common.clear')}
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {visibleIcons.length === 0 ? (
          <div className="mt-4 rounded-lg border border-dashed border-border bg-secondary/30 px-4 py-8 text-center text-sm text-muted-foreground">
            {t('page.workflow_templates.icon_picker_empty')}
          </div>
        ) : (
          <div className="mt-4 max-h-[56vh] overflow-y-auto pr-1">
            <div className="grid grid-cols-4 gap-1.5 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10">
              {visibleIcons.map(({ name, Icon }) => {
                const selected = selectedIcon === name;
                return (
                  <Tooltip key={name} content={name}>
                    <button
                      type="button"
                      onClick={() => onSelect(name)}
                      aria-label={name}
                      className={cn(
                        'inline-flex h-12 w-full items-center justify-center rounded-md border p-1 transition-colors',
                        selected
                          ? 'border-primary bg-primary/10 text-primary'
                          : 'border-border bg-background text-foreground hover:bg-accent',
                      )}
                    >
                      <Icon className="h-5 w-5" />
                    </button>
                  </Tooltip>
                );
              })}
            </div>
          </div>
        )}

        <div className="mt-5 flex justify-end">
          <button
            type="button"
            onClick={handleClose}
            className="inline-flex items-center justify-center rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all"
          >
            {t('common.close')}
          </button>
        </div>
      </div>
    </div>
  );
}
