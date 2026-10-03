/** Locale-aware formatting helpers (pure, unit-tested). */
import type { Locale } from './i18n/core';

const INTL_LOCALE: Record<Locale, string> = { fr: 'fr-FR', en: 'en-GB' };

export function formatPercent(probability: number, locale: Locale): string {
  return new Intl.NumberFormat(INTL_LOCALE[locale], {
    style: 'percent',
    maximumFractionDigits: 0,
  }).format(probability);
}

/**
 * Decimal "odds" (1 / p), the way betting sites show them. Capped at 99 and
 * shown as "—" for a null probability.
 */
export function formatOdds(probability: number, locale: Locale): string {
  if (probability <= 0) return '—';
  const odds = Math.min(99, 1 / probability);
  return new Intl.NumberFormat(INTL_LOCALE[locale], {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(odds);
}

export function formatNumber(value: number, locale: Locale, decimals = 0): string {
  return new Intl.NumberFormat(INTL_LOCALE[locale], {
    minimumFractionDigits: 0,
    maximumFractionDigits: decimals,
  }).format(value);
}

/** Driver value with its unit, e.g. "12,5 cm". Strings are shown as-is. */
export function formatDriver(
  value: number | string | null | undefined,
  locale: Locale,
  unit?: string | null,
  decimals = 0,
): string | null {
  if (value === null || value === undefined) return null;
  const text = typeof value === 'number' ? formatNumber(value, locale, decimals) : value;
  return unit ? `${text} ${unit}` : text;
}

/** "dimanche 14 décembre" / "Sunday 14 December" for a YYYY-MM-DD date. */
export function formatLongDate(isoDate: string, locale: Locale): string {
  const [year, month, day] = isoDate.split('-').map(Number);
  const date = new Date(Date.UTC(year ?? 1970, (month ?? 1) - 1, day ?? 1, 12));
  return new Intl.DateTimeFormat(INTL_LOCALE[locale], {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    timeZone: 'UTC',
  }).format(date);
}

/** "06:32" for an ISO datetime, in the given IANA timezone. */
export function formatTime(isoDateTime: string, locale: Locale, timeZone: string): string {
  return new Intl.DateTimeFormat(INTL_LOCALE[locale], {
    hour: '2-digit',
    minute: '2-digit',
    timeZone,
  }).format(new Date(isoDateTime));
}

/** "22:00 → 09:00", with the day when the window spans several days. */
export function formatWindow(
  startIso: string,
  endIso: string,
  locale: Locale,
  timeZone: string,
): string {
  const start = new Date(startIso);
  const end = new Date(endIso);
  const sameDay =
    new Intl.DateTimeFormat('en-CA', { timeZone }).format(start) ===
    new Intl.DateTimeFormat('en-CA', { timeZone }).format(end);
  const time = (date: Date) => formatTime(date.toISOString(), locale, timeZone);
  if (sameDay) return `${time(start)} → ${time(end)}`;
  const day = new Intl.DateTimeFormat(INTL_LOCALE[locale], { weekday: 'short', timeZone });
  return `${day.format(start)} ${time(start)} → ${day.format(end)} ${time(end)}`;
}
