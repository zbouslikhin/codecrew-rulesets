# svelte-feature

## v1.1.0

- ESLint and ast-grep report in SARIF: problems come with exact positions (line and
  column, start and end) and a severity; only errors block, warnings are shown.
- svelte-check through a declarative parser (it has no SARIF output).
- ast-grep rules moved to `.codecrew/rulesets/svelte-feature/ast-grep/`, so several
  rulesets can live in one repository.
- `eslint.config.js` follows the ruleset's own Prettier settings.
- New devDependency: `@microsoft/eslint-formatter-sarif`. Setup falls back from
  `npm ci` to `npm install` while `package-lock.json` doesn't list it yet; commit the
  updated lock file afterwards.

## v1.0.0

The ruleset as it was built into codecrew: feature-folder structure, Prettier, ESLint
(no `../` imports, T-prefixed types in `.svelte`), ast-grep (T-prefixed types in `.ts`),
svelte-check. `npm ci` as setup, Vite dev server as preview.
