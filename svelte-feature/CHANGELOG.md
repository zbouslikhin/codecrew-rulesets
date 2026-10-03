# svelte-feature

## v2.5.0

- Skill `feature-pattern`: the layout of a feature, file by file, with the code each file starts
  from. Agents see it in their list of skills and load it with `read_skill`. Needs a codecrew with skills; older versions don't install the folder.

## v2.4.0

- Permission rules. Denied: `npm publish`, `git push`, `git commit`. Needs you (refused for
  now): adding or removing a dependency (`npm install <package>`, `npm uninstall`), `npx`,
  writing package.json. Allowed, also for agents that only run allowed commands: `npm install`,
  `npm ci`, `npm run`, `npm test`, the project's own tools, `node`, read-only git.
- Proven by `fixtures/permissions.yaml`. Needs a codecrew with permission rules; older versions ignore the section.

## v2.3.0

- Plan mode: a plan lists its files, new features, tests and interface changes. Plan checks:
  every new feature has a planned test (`feature-has-test`), new files and tests fit the
  structure rules, interface changes make a plan risky ("ask on risk" asks first).
- The Svelte developer template starts with plan mode *automatic*.
- Proven by `fixtures/plans/`. Needs a codecrew with plan mode; older versions ignore the section.

## v2.2.0

- Repo map: agents get what each TypeScript file exports up front.

## v2.1.0

- Project template (`template/`): `codecrew new-project --ruleset svelte-feature` creates a
  Svelte 5 + TypeScript app with the feature-folder layout, a welcome feature and its test.
- Agent templates: Svelte developer and Svelte tester.

## v2.0.1

- `.codecrew/.gitattributes` pins LF for the ruleset's own files, so Git for Windows
  (core.autocrlf) doesn't rewrite them with CRLF. (codecrew itself also ignores
  line-ending differences when comparing rule files.)

## v2.0.0

Breaking: projects need tests now.

- Every feature needs at least one test (`*.test.ts`), run with Vitest + Testing Library.
- Every feature must be reachable through imports from `src/main.ts`: a feature that
  nothing uses fails, even with passing tests.
- `vite build` must succeed.
- New devDependencies: vitest, @testing-library/svelte, jsdom, sass. New file: `vitest.config.ts`.

Upgrading: add a test to each feature (a component test that renders it is enough), then update.

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
