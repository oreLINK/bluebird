// Generate TypeScript types from the JSON Schemas exported by the pipeline
// (`uv run bluebird schemas`). Run with `npm run gen:types`; CI fails if the
// committed files in src/lib/generated/ are out of date.
import { readdir, readFile, writeFile, mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { compile } from 'json-schema-to-typescript';

const schemaDir = fileURLToPath(new URL('../../config/schemas/', import.meta.url));
const outDir = fileURLToPath(new URL('../src/lib/generated/', import.meta.url));

await mkdir(outDir, { recursive: true });
const files = (await readdir(schemaDir)).filter((f) => f.endsWith('.schema.json')).sort();

for (const file of files) {
  const schema = JSON.parse(await readFile(schemaDir + file, 'utf8'));
  delete schema.$schema;
  delete schema.$comment;
  const name = file.replace('.schema.json', '');
  const ts = await compile(schema, schema.title ?? name, {
    bannerComment: `/* Generated from config/schemas/${file} by \`npm run gen:types\`. Do not edit. */`,
    additionalProperties: false,
    style: { singleQuote: true, printWidth: 100 },
  });
  await writeFile(`${outDir}${name}.ts`, ts);
  console.log(`wrote src/lib/generated/${name}.ts`);
}
