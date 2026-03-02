function parseDate(value: string | Date): Date | null {
  const date = value instanceof Date ? value : new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function pad(n: number): string {
  return String(n).padStart(2, '0');
}

export function formatDate(value: string | Date | null | undefined): string {
  if (!value) return '-';
  const date = parseDate(value);
  if (!date) return '-';

  const year = date.getFullYear();
  const month = pad(date.getMonth() + 1);
  const day = pad(date.getDate());
  return `${year}/${month}/${day}`;
}

export function formatRelativeDate(
  value: string | Date | null | undefined,
  t: (key: string) => string,
): string {
  if (!value) return '';
  const date = parseDate(value);
  if (!date) return '';

  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const target = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const diffDays = Math.floor((today.getTime() - target.getTime()) / 86400000);

  if (diffDays === 0) return t('date.today');
  if (diffDays === 1) return t('date.yesterday');

  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

export function formatDateTime(value: string | Date | null | undefined): string {
  if (!value) return '-';
  const date = parseDate(value);
  if (!date) return '-';

  const year = date.getFullYear();
  const month = pad(date.getMonth() + 1);
  const day = pad(date.getDate());
  const hours = pad(date.getHours());
  const minutes = pad(date.getMinutes());

  return `${year}/${month}/${day} ${hours}:${minutes}`;
}
