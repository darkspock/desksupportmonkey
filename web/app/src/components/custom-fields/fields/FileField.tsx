import { useRef, useState } from 'react';
import api from '../../../lib/api';
import { useI18n } from '../../../lib/i18n';
import type { CustomFieldDefinition, CustomFieldFile } from '../../../types';

const MAX_SIZE = 10 * 1024 * 1024; // 10 MB
const MAX_FILES = 10;
const ACCEPT = '.pdf,.jpg,.jpeg,.png,.gif,.webp,.zip';

interface Props {
  definition: CustomFieldDefinition;
  value: unknown;
  onChange: (value: unknown) => void;
  entityType?: string;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function isImageMime(mime: string): boolean {
  return mime.startsWith('image/');
}

function mimeIcon(mime: string): string {
  if (mime === 'application/pdf') return 'PDF';
  if (mime === 'application/zip') return 'ZIP';
  if (mime.startsWith('image/')) return 'IMG';
  return 'FILE';
}

export function FileField({ definition, value, onChange, entityType = 'asset' }: Props) {
  const { t } = useI18n();
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const files: CustomFieldFile[] = Array.isArray(value) ? (value as CustomFieldFile[]) : [];

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files;
    if (!selected?.length) return;

    setError(null);

    if (files.length + selected.length > MAX_FILES) {
      setError(t('page.custom_fields.file_max_reached'));
      if (inputRef.current) inputRef.current.value = '';
      return;
    }

    setUploading(true);
    const newFiles: CustomFieldFile[] = [...files];

    try {
      for (const file of Array.from(selected)) {
        if (file.size > MAX_SIZE) {
          setError(t('page.custom_fields.file_too_large'));
          continue;
        }

        const formData = new FormData();
        formData.append('file', file);

        const { data } = await api.post(
          `/custom-fields/files/upload?entity_type=${entityType}&field_key=${definition.field_key}`,
          formData,
          { headers: { 'Content-Type': 'multipart/form-data' } },
        );

        newFiles.push(data.data as CustomFieldFile);
      }

      onChange(newFiles.length ? newFiles : null);
    } catch {
      setError(t('page.custom_fields.file_upload_error'));
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = '';
    }
  };

  const handleRemove = (fileId: string) => {
    const next = files.filter((f) => f.id !== fileId);
    onChange(next.length ? next : null);
  };

  const handleDownload = async (file: CustomFieldFile) => {
    try {
      const downloadPath =
        file.download_path ||
        `/custom-fields/files/${file.id}/download?key=${encodeURIComponent(file.key)}`;
      const { data } = await api.get(downloadPath);
      window.open(data.data.url, '_blank');
    } catch {
      // silent
    }
  };

  return (
    <div>
      <label className="mb-1.5 block text-sm text-muted-foreground">
        {definition.label}
        {definition.required && <span className="text-destructive"> *</span>}
      </label>

      {/* File list */}
      {files.length > 0 && (
        <div className="mb-2 space-y-1.5">
          {files.map((f) => (
            <div
              key={f.id}
              className="flex items-center gap-2 rounded-md border border-border bg-card px-3 py-2 text-sm"
            >
              {isImageMime(f.mime) ? (
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-blue-50 text-xs font-semibold text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
                  IMG
                </span>
              ) : (
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-gray-100 text-xs font-semibold text-gray-600 dark:bg-gray-800 dark:text-gray-300">
                  {mimeIcon(f.mime)}
                </span>
              )}
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
              <button
                type="button"
                onClick={() => handleRemove(f.id)}
                className="shrink-0 text-xs text-red-600 hover:underline dark:text-red-400"
              >
                {t('page.custom_fields.file_remove')}
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Upload button */}
      {files.length < MAX_FILES && (
        <div>
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPT}
            multiple
            onChange={handleUpload}
            className="hidden"
            disabled={uploading}
          />
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            disabled={uploading}
            className="inline-flex items-center rounded-md border border-border bg-card px-3 py-1.5 text-sm text-foreground hover:bg-muted disabled:opacity-50"
          >
            {uploading ? t('page.custom_fields.file_uploading') : t('page.custom_fields.file_upload')}
          </button>
        </div>
      )}

      {error && <p className="mt-1 text-xs text-destructive">{error}</p>}

      {definition.description && (
        <p className="mt-1 text-xs text-muted-foreground">{definition.description}</p>
      )}
      <p className="mt-0.5 text-xs text-muted-foreground">
        {t('page.custom_fields.file_upload_hint')}
      </p>
    </div>
  );
}
