/// <reference types="svelte" />
/// <reference types="vite/client" />

// YAML files are bundled by @rollup/plugin-yaml. Their shapes are checked
// by the pipeline (`bluebird validate`) and typed in src/lib/config.ts.
declare module '*.yaml' {
  const data: unknown;
  export default data;
}
