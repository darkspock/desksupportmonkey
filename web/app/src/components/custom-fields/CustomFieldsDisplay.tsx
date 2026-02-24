import api from '../../lib/api';
import { useI18n } from '../../lib/i18n';
import { formatDate } from '../../lib/date';
import type { CustomFieldFile, CustomFieldValue } from '../../types';

interface CustomFieldsDisplayProps {
  customFields: CustomFieldValue[];
}

export function CustomFieldsDisplay({ customFields }: CustomFieldsDisplayProps) {
  const { t } = useI18n();

  if (!customFields.length) return null;

  return (
    <div className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
      {customFields.map((cf) => {
        const inactive = !cf.is_active;
        const missingRequired = cf.required && (cf.value == null || cf.value === '');
        const fullWidth = cf.type === 'file' || cf.type === 'multi_select';

        return (
          <div key={cf.key} className={`${fullWidth ? 'sm:col-span-2' : ''}${inactive ? ' opacity-50' : ''}`}>
            <span className="text-muted-foreground">
              {cf.label}
              {inactive && (
                <span className="ml-1.5 inline-flex items-center rounded bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
                  {t('page.custom_fields.inactive_field')}
                </span>
              )}
              :
            </span>{' '}
            {missingRequired ? (
              <span className="font-medium text-amber-600 dark:text-amber-400">
                {t('page.custom_fields.missing_required')}
              </span>
            ) : (
              <span className="text-foreground">{renderValue(cf, t)}</span>
            )}
          </div>
        );
      })}
    </div>
  );
}

function renderValue(
  cf: CustomFieldValue,
  t: (key: string) => string,
): React.ReactNode {
  if (cf.value == null || cf.value === '') {
    return t('page.custom_fields.no_value');
  }

  if (cf.type === 'boolean') {
    return cf.value ? t('page.custom_fields.yes') : t('page.custom_fields.no');
  }

  if (cf.type === 'date' && typeof cf.value === 'string') {
    return formatDate(cf.value);
  }

  if (cf.type === 'multi_select' && Array.isArray(cf.value)) {
    return (
      <span className="inline-flex flex-wrap gap-1">
        {(cf.value as string[]).map((v) => (
          <span
            key={v}
            className="inline-flex items-center rounded bg-muted px-2 py-0.5 text-xs font-medium text-foreground"
          >
            {v}
          </span>
        ))}
      </span>
    );
  }

  if (cf.type === 'file' && Array.isArray(cf.value)) {
    const files = cf.value as CustomFieldFile[];
    if (!files.length) return t('page.custom_fields.file_no_files');
    return <FileList files={files} />;
  }

  return String(cf.value);
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function mimeIcon(mime: string): string {
  if (mime === 'application/pdf') return 'PDF';
  if (mime === 'application/zip') return 'ZIP';
  if (mime.startsWith('image/')) return 'IMG';
  return 'FILE';
}

function FileList({ files }: { files: CustomFieldFile[] }) {
  const { t } = useI18n();

  const handleDownload = async (f: CustomFieldFile) => {
    try {
      const path =
        f.download_path ||
        `/custom-fields/files/${f.id}/download?key=${encodeURIComponent(f.key)}`;
      const { data } = await api.get(path);
      window.open(data.data.url, '_blank');
    } catch {
      // silent
    }
  };

  return (
    <div className="mt-1 space-y-1.5">
      {files.map((f) => (
        <div
          key={f.id}
          className="flex items-center gap-2 rounded-md border border-border bg-card px-3 py-2 text-sm"
        >
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-gray-100 text-xs font-semibold text-gray-600 dark:bg-gray-800 dark:text-gray-300">
            {mimeIcon(f.mime)}
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate font-medium text-foreground">{f.name}</p>
            <p className="text-xs text-muted-foreground">{formatSize(f.size)}</p>
          </div>
          <button
            type="button"
            onClick={() => handleDownload(f)}
            className="shrink-0 text-xs text-blue-600 hover:underline dark:text-blue-400"
          >
            {t('page.custom_fields.file_download')}
          </button>
        </div>
      ))}
    </div>
  );
}
