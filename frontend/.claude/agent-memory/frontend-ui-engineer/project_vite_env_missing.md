---
name: vite-env.d.ts was missing
description: src/vite-env.d.ts did not exist, causing TS2339 error on import.meta.env in client.ts — blocked all builds
type: project
---

`src/vite-env.d.ts` was absent from the repo. `tsconfig.json` also lacked `"types": ["vite/client"]`. The fix was to create `src/vite-env.d.ts` with `/// <reference types="vite/client" />`. File is now committed.

**Why:** Vite projects need either the triple-slash reference or a tsconfig types entry so TypeScript knows about `ImportMeta.env`.

**How to apply:** If a build fails with TS2339 on `import.meta.env`, check for this file first before touching tsconfig.
