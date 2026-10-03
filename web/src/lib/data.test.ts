import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { DataError, type MassifDaily, latestUrl, loadMassif, todayIn } from './data';

const demo = JSON.parse(
  readFileSync(new URL('../../public/data/diamond/pyrenees/latest.json', import.meta.url), 'utf8'),
) as MassifDaily;

const respond = (status: number, body: unknown = {}) =>
  (async () => new Response(JSON.stringify(body), { status })) as unknown as typeof fetch;

describe('data', () => {
  it('builds relative URLs that work under any Pages sub-path', () => {
    expect(latestUrl('pyrenees', './')).toBe('./data/diamond/pyrenees/latest.json');
  });

  it('loads a payload, maps 404 to null and rejects other errors', async () => {
    await expect(loadMassif('pyrenees', respond(200, demo))).resolves.toMatchObject({
      massif_id: 'pyrenees',
    });
    await expect(loadMassif('pyrenees', respond(404))).resolves.toBeNull();
    await expect(loadMassif('pyrenees', respond(500))).rejects.toBeInstanceOf(DataError);
    await expect(
      loadMassif('pyrenees', respond(200, { ...demo, schema_version: 99 })),
    ).rejects.toThrow('unsupported schema_version');
  });

  it('demo payload rankings are sorted by probability', () => {
    for (const kpi of Object.values(demo.kpis)) {
      const probabilities = kpi.ranking.map((r) => r.probability);
      expect(probabilities).toEqual([...probabilities].sort((a, b) => b - a));
    }
  });

  it('computes today in a timezone', () => {
    expect(todayIn('Europe/Paris', new Date('2026-12-13T23:30:00Z'))).toBe('2026-12-14');
  });
});
