import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { kpis } from './config';
import {
  DataError,
  type MassifDaily,
  latestUrl,
  loadMassif,
  loadStatus,
  statusUrl,
  todayIn,
} from './data';

const demo = JSON.parse(
  readFileSync(new URL('../../public/data/diamond/pyrenees/latest.json', import.meta.url), 'utf8'),
) as MassifDaily;

const respond = (status: number, body: unknown = {}) =>
  (async () => new Response(JSON.stringify(body), { status })) as unknown as typeof fetch;

describe('data', () => {
  it('builds relative URLs that work under any Pages sub-path', () => {
    expect(latestUrl('pyrenees', './')).toBe('./data/diamond/pyrenees/latest.json');
    expect(statusUrl('./')).toBe('./data/diamond/status.json');
  });

  it('loads the service status with its own schema version', async () => {
    const status = JSON.parse(
      readFileSync(new URL('../../public/data/diamond/status.json', import.meta.url), 'utf8'),
    );
    await expect(loadStatus(respond(200, status))).resolves.toMatchObject({ state: 'ok' });
    await expect(loadStatus(respond(404))).resolves.toBeNull();
    await expect(loadStatus(respond(200, { ...status, schema_version: 2 }))).rejects.toThrow(
      'unsupported schema_version',
    );
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

  it('demo payload rankings follow the KPI display, periods by start', () => {
    for (const [id, kpi] of Object.entries(demo.kpis)) {
      const starts = kpi.periods.map((p) => Date.parse(p.start));
      expect(starts).toEqual([...starts].sort((a, b) => a - b));
      const config = kpis.find((k) => k.id === id);
      const driver = config?.display?.kind === 'value' ? config.display.driver : undefined;
      const sign = config?.order === 'asc' ? 1 : -1;
      for (const period of kpi.periods) {
        // A value display ranks by the shown value (`order`), the others by probability.
        const keys = period.ranking.map((r) => (driver ? Number(r.drivers[driver]) : r.probability));
        expect(keys).toEqual([...keys].sort((a, b) => sign * (a - b)));
      }
    }
  });

  it('computes today in a timezone', () => {
    expect(todayIn('Europe/Paris', new Date('2026-12-13T23:30:00Z'))).toBe('2026-12-14');
  });
});
