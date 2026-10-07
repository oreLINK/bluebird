/** Accessible one-line summary of a ranked station, shared by the tile rows. */
import { type KpiView, type RankItem, itemLabel, itemNote } from '../lib/kpiView';
import type { Locale } from '../lib/i18n/core';

interface Translator {
  locale: Locale;
  // Method syntax: accepts the i18n store, whose keys are a narrower union.
  t(key: string, params?: Record<string, string | number>): string;
}

/**
 * "1. Cauterets, 82 %, high confidence", "1. Porté, −24 °C (risque modéré), …"
 * (live) or "1. La Pierre Saint-Martin, 4,43 m".
 */
export function itemSummary(
  view: KpiView,
  item: RankItem,
  rank: number,
  station: string,
  i18n: Translator,
): string {
  const note = itemNote(item, i18n.locale);
  const label = itemLabel(view, item, i18n.locale);
  const text = i18n.t('a11y.rowSummary', {
    rank,
    station,
    percent: note ? `${label} (${note})` : label,
  });
  if (!item.confidence) return text;
  return `${text}, ${i18n.t('a11y.confidence', { level: i18n.t(`confidence.${item.confidence}`) })}`;
}
