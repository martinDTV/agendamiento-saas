import { format, parseISO } from 'date-fns';
import { es } from 'date-fns/locale';

export function formatLongDate(iso: string): string {
  try {
    return format(parseISO(iso), "EEEE d 'de' MMMM", { locale: es });
  } catch {
    return iso;
  }
}

export function formatShortDate(iso: string): string {
  try {
    return format(parseISO(iso), 'd MMM yyyy', { locale: es });
  } catch {
    return iso;
  }
}

export function formatTime(hhmm: string): string {
  // "14:30" → "2:30 p. m."
  const [h, m] = hhmm.split(':').map(Number);
  if (Number.isNaN(h) || Number.isNaN(m)) return hhmm;
  const period = h >= 12 ? 'p. m.' : 'a. m.';
  const h12 = ((h + 11) % 12) + 1;
  return `${h12}:${String(m).padStart(2, '0')} ${period}`;
}

export function formatCurrency(amount: number | null | undefined): string {
  if (amount == null) return '—';
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN',
    maximumFractionDigits: 0,
  }).format(amount);
}
